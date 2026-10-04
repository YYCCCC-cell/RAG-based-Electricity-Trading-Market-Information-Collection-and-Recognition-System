"""Command-line interface for crawling, running, querying and evaluating."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from .crawler import crawl
from .evaluation import evaluate_all
from .io import read_notices, write_json, write_notices
from .pipeline import build_digest, process
from .retriever import BM25Index, answer


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = ROOT / "data" / "labels" / "notices_labeled.csv"
DEFAULT_QUESTIONS = ROOT / "data" / "evals" / "questions.jsonl"


def cmd_crawl(args: argparse.Namespace) -> int:
    notices = crawl(limit=args.limit, delay_seconds=args.delay)
    write_notices(args.output, notices)
    print(f"saved {len(notices)} public notices to {args.output}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    notices = read_notices(args.data)
    if not notices:
        raise ValueError(f"no notices found in {args.data}")
    rows = process(notices)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "predictions.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output / "daily_digest.md").write_text(build_digest(rows), encoding="utf-8")
    print(f"processed {len(rows)} notices; outputs written to {output}")
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    metrics = evaluate_all(read_notices(args.data), args.questions)
    write_json(args.output, metrics)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0


def cmd_ask(args: argparse.Namespace) -> int:
    result = answer(BM25Index(read_notices(args.data)), args.question, top_k=args.top_k)
    print(result["answer"])
    for citation in result["citations"]:
        print(f"  {citation['notice_id']}: {citation['url']}")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    from .server import serve

    serve(args.data, host=args.host, port=args.port)
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Power Notice Radar")
    sub = root.add_subparsers(dest="command", required=True)

    crawl_parser = sub.add_parser("crawl", help="crawl public notices")
    crawl_parser.add_argument("--limit", type=int, default=100)
    crawl_parser.add_argument("--delay", type=float, default=0.15)
    crawl_parser.add_argument("--output", default=ROOT / "data" / "raw" / "notices_snapshot.csv")
    crawl_parser.set_defaults(func=cmd_crawl)

    run_parser = sub.add_parser("run", help="classify notices and build a digest")
    run_parser.add_argument("--data", default=DEFAULT_DATA)
    run_parser.add_argument("--output", default=ROOT / "outputs")
    run_parser.set_defaults(func=cmd_run)

    eval_parser = sub.add_parser("evaluate", help="run documented evaluations")
    eval_parser.add_argument("--data", default=DEFAULT_DATA)
    eval_parser.add_argument("--questions", default=DEFAULT_QUESTIONS)
    eval_parser.add_argument("--output", default=ROOT / "outputs" / "metrics.json")
    eval_parser.set_defaults(func=cmd_evaluate)

    ask_parser = sub.add_parser("ask", help="ask a citation-backed question")
    ask_parser.add_argument("question")
    ask_parser.add_argument("--data", default=DEFAULT_DATA)
    ask_parser.add_argument("--top-k", type=int, default=3)
    ask_parser.set_defaults(func=cmd_ask)

    serve_parser = sub.add_parser("serve", help="start the local demo UI")
    serve_parser.add_argument("--data", default=DEFAULT_DATA)
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)
    serve_parser.set_defaults(func=cmd_serve)
    return root


def main() -> None:
    args = parser().parse_args()
    try:
        raise SystemExit(args.func(args))
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
