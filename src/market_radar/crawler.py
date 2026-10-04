"""Crawler for the public latest-notices pages of Guangzhou Power Exchange Center."""

from __future__ import annotations

import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser

from .models import Notice


BASE_URL = "http://www.gzpec.cn/information/zxtz/"
USER_AGENT = "PowerNoticeRadar/1.0 (public-notice research; low-rate crawler)"


def _strip_html(fragment: str) -> str:
    fragment = re.sub(r"<style.*?</style>", " ", fragment, flags=re.S | re.I)
    fragment = re.sub(r"<script.*?</script>", " ", fragment, flags=re.S | re.I)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", unescape(fragment)).strip()


class ListingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.entries: list[tuple[str, str]] = []
        self._active_href: str | None = None
        self._active_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        values = dict(attrs)
        href = values.get("href") or ""
        if re.search(r"\./20\d{4}/t20\d{6}_\d+\.html", href):
            self._active_href = href
            self._active_text = []

    def handle_data(self, data: str) -> None:
        if self._active_href and data.strip():
            self._active_text.append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._active_href:
            title = " ".join(self._active_text).strip()
            if title:
                self.entries.append((self._active_href, title))
            self._active_href = None
            self._active_text = []


def _fetch(url: str, timeout: int = 15, attempts: int = 3) -> str:
    if urllib.parse.urlparse(url).scheme not in {"http", "https"}:
        raise ValueError(f"unsupported URL scheme: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Connection": "close"})
    error: Exception | None = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read().decode("utf-8", errors="replace")
        except Exception as exc:
            error = exc
            time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url} after {attempts} attempts") from error


def discover(limit: int = 100, delay_seconds: float = 0.15) -> list[tuple[str, str]]:
    return discover_section(BASE_URL, 27, limit, delay_seconds)


def discover_section(
    base_url: str,
    page_count: int,
    limit: int,
    delay_seconds: float = 0.15,
) -> list[tuple[str, str]]:
    if limit <= 0 or page_count <= 0:
        return []
    if delay_seconds < 0:
        raise ValueError("delay_seconds must be non-negative")
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    for page in range(page_count):
        parser = ListingParser()
        page_url = base_url if page == 0 else f"{base_url}index_{page}.html"
        parser.feed(_fetch(page_url))
        for href, title in parser.entries:
            url = urllib.parse.urljoin(base_url, href)
            if url not in seen:
                seen.add(url)
                found.append((url, title))
            if len(found) >= limit:
                return found
        time.sleep(delay_seconds)
    return found


def parse_article(url: str, fallback_title: str = "") -> tuple[str, str, str]:
    html = _fetch(url)
    title_match = re.search(r'<h3 class="title">(.*?)</h3>', html, flags=re.S | re.I)
    title = _strip_html(title_match.group(1)) if title_match else fallback_title
    date_match = re.search(r"发布时间[：:]\s*(\d{4}-\d{2}-\d{2})", html)
    date = date_match.group(1) if date_match else ""
    body_match = re.search(r'<div class="txt">(.*?)<div style="padding:', html, flags=re.S | re.I)
    body = _strip_html(body_match.group(1)) if body_match else title
    return title, date, body


def crawl(limit: int = 100, delay_seconds: float = 0.15) -> list[Notice]:
    entries = discover(limit=limit, delay_seconds=delay_seconds)
    fetched_at = datetime.now(timezone.utc).isoformat()
    notices: list[Notice] = []
    for index, (url, fallback_title) in enumerate(entries, start=1):
        try:
            title, date, body = parse_article(url, fallback_title)
        except (OSError, RuntimeError, TimeoutError, ValueError):
            title, date, body = fallback_title, "", fallback_title
        notices.append(
            Notice(
                notice_id=f"GZPEC-{index:03d}",
                title=title,
                published_date=date,
                url=url,
                body=body,
                source_section="latest_notices",
                fetched_at=fetched_at,
            )
        )
        time.sleep(delay_seconds)
    return notices
