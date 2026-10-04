"""Lightweight BM25 retrieval and citation-bound extractive Q&A."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from .models import Notice


ASCII_WORD = re.compile(r"[A-Za-z0-9_]+")
HAN_RUN = re.compile(r"[\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    tokens = [m.group(0).lower() for m in ASCII_WORD.finditer(text)]
    for run in HAN_RUN.findall(text):
        tokens.extend(run[i : i + 2] for i in range(max(1, len(run) - 1)))
        tokens.extend(char for char in run if char in "年月日时前后交易结算规则申报绿电绿证")
    return tokens


@dataclass(slots=True)
class Hit:
    notice: Notice
    score: float


class BM25Index:
    def __init__(self, notices: list[Notice], k1: float = 1.5, b: float = 0.75):
        self.notices = notices
        self.k1 = k1
        self.b = b
        self.docs = [Counter(tokenize(n.text)) for n in notices]
        self.lengths = [sum(doc.values()) for doc in self.docs]
        self.avgdl = sum(self.lengths) / max(1, len(self.lengths))
        df: Counter[str] = Counter()
        for doc in self.docs:
            df.update(doc.keys())
        n = len(notices)
        self.idf = {term: math.log(1 + (n - freq + 0.5) / (freq + 0.5)) for term, freq in df.items()}

    def search(self, query: str, top_k: int = 5) -> list[Hit]:
        q = Counter(tokenize(query))
        scored: list[Hit] = []
        for notice, doc, dl in zip(self.notices, self.docs, self.lengths):
            score = 0.0
            for term, qtf in q.items():
                tf = doc.get(term, 0)
                if not tf:
                    continue
                denom = tf + self.k1 * (1 - self.b + self.b * dl / max(1.0, self.avgdl))
                score += self.idf.get(term, 0.0) * tf * (self.k1 + 1) / denom * min(qtf, 2)
            if score > 0:
                scored.append(Hit(notice, round(score, 4)))
        return sorted(scored, key=lambda hit: (hit.score, hit.notice.published_date), reverse=True)[:top_k]


def _best_excerpt(notice: Notice, query: str, limit: int = 180) -> str:
    terms = set(tokenize(query))
    sentences = [s.strip() for s in re.split(r"[。！？\n]+", notice.body) if s.strip()]
    if not sentences:
        return notice.title
    best = max(sentences, key=lambda s: len(terms & set(tokenize(s))))
    return best[:limit] + ("…" if len(best) > limit else "")


def answer(index: BM25Index, query: str, top_k: int = 3) -> dict[str, object]:
    hits = index.search(query, top_k=top_k)
    if not hits:
        return {
            "answer": "在当前快照中没有检索到足够相关的公开通知。请换用通知标题中的关键词。",
            "citations": [],
            "grounded": True,
        }
    lines = [f"- {_best_excerpt(hit.notice, query)} [{hit.notice.notice_id}]" for hit in hits]
    return {
        "answer": "根据检索到的公开通知：\n" + "\n".join(lines),
        "citations": [
            {
                "notice_id": hit.notice.notice_id,
                "title": hit.notice.title,
                "url": hit.notice.url,
                "score": hit.score,
            }
            for hit in hits
        ],
        "grounded": True,
    }

