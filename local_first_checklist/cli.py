from __future__ import annotations

import argparse
from pathlib import Path

from .core import Checklist, default_data_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage a local-first checklist.")
    parser.add_argument("--data", type=Path, default=default_data_path(), help="Path to the JSON data file.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a checklist item.")
    add_parser.add_argument("title", help="Item title.")

    done_parser = subparsers.add_parser("done", help="Mark an item as done.")
    done_parser.add_argument("id", type=int, help="Item id.")

    list_parser = subparsers.add_parser("list", help="List checklist items.")
    list_parser.add_argument("--all", action="store_true", help="Include completed items.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    checklist = Checklist(args.data)

    if args.command == "add":
        item = checklist.add(args.title)
        print(f"added #{item.id}: {item.title}")
        return 0

    if args.command == "done":
        try:
            item = checklist.complete(args.id)
        except KeyError as exc:
            parser.error(str(exc))
        print(f"done #{item.id}: {item.title}")
        return 0

    if args.command == "list":
        items = checklist.list(include_done=args.all)
        if not items:
            print("no items")
            return 0
        for item in items:
            marker = "x" if item.done else " "
            print(f"[{marker}] #{item.id} {item.title}")
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

