from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from . import __version__
from .core import (
    Checklist,
    ChecklistError,
    ChecklistItem,
    default_data_path,
    item_to_dict,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage a reliable local-first checklist.")
    parser.add_argument("--data", type=Path, default=default_data_path(), help="Path to the JSON data file.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--version", action="version", version=f"local-first-checklist {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a checklist item.")
    add_parser.add_argument("title", help="Item title.")

    done_parser = subparsers.add_parser("done", help="Mark an item as done.")
    done_parser.add_argument("id", type=int, help="Item id.")

    reopen_parser = subparsers.add_parser("reopen", help="Reopen a completed item.")
    reopen_parser.add_argument("id", type=int, help="Item id.")

    edit_parser = subparsers.add_parser("edit", help="Replace an item title.")
    edit_parser.add_argument("id", type=int, help="Item id.")
    edit_parser.add_argument("title", help="New item title.")

    remove_parser = subparsers.add_parser("remove", help="Permanently remove an item.")
    remove_parser.add_argument("id", type=int, help="Item id.")
    remove_parser.add_argument("--yes", action="store_true", help="Confirm permanent removal.")

    list_parser = subparsers.add_parser("list", help="List checklist items.")
    list_parser.add_argument("--all", action="store_true", help="Include completed items.")

    subparsers.add_parser("doctor", help="Inspect primary and backup data without modifying them.")
    recover_parser = subparsers.add_parser("recover", help="Replace the primary file with its validated backup.")
    recover_parser.add_argument("--yes", action="store_true", help="Confirm recovery.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in {"remove", "recover"} and not args.yes:
        return _error(args, f"{args.command} requires --yes", 2)

    try:
        if args.command == "doctor":
            report = Checklist.diagnose(args.data)
            if args.json:
                _print_json(report.to_dict())
            else:
                print(f"primary: {report.primary.status} ({report.primary.path})")
                print(f"backup: {report.backup.status} ({report.backup.path})")
                for health in (report.primary, report.backup):
                    if health.detail:
                        print(f"{health.status}: {health.detail}")
            return 0 if report.healthy else 1

        if args.command == "recover":
            report = Checklist.recover(args.data)
            if args.json:
                _print_json({"action": "recovered", **report.to_dict()})
            else:
                print(f"recovered: {args.data.expanduser()}")
            return 0

        checklist = Checklist(args.data)

        if args.command == "add":
            return _item_result(args, "added", checklist.add(args.title))
        if args.command == "done":
            return _item_result(args, "completed", checklist.complete(args.id))
        if args.command == "reopen":
            return _item_result(args, "reopened", checklist.reopen(args.id))
        if args.command == "edit":
            return _item_result(args, "edited", checklist.edit(args.id, args.title))
        if args.command == "remove":
            return _item_result(args, "removed", checklist.remove(args.id))
        if args.command == "list":
            items = checklist.list(include_done=args.all)
            if args.json:
                _print_json({"count": len(items), "items": [item_to_dict(item) for item in items]})
            elif not items:
                print("no items")
            else:
                for item in items:
                    marker = "x" if item.done else " "
                    print(f"[{marker}] #{item.id} {item.title}")
            return 0
    except (ChecklistError, OSError) as exc:
        return _error(args, str(exc), 1)

    return _error(args, "unknown command", 2)


def _item_result(args: argparse.Namespace, action: str, item: ChecklistItem) -> int:
    item_payload = item_to_dict(item)
    if args.json:
        _print_json({"action": action, "item": item_payload})
    else:
        print(f"{action} #{item_payload['id']}: {item_payload['title']}")
    return 0


def _error(args: argparse.Namespace, message: str, exit_code: int) -> int:
    if getattr(args, "json", False):
        print(json.dumps({"error": message, "exit_code": exit_code}, ensure_ascii=False), file=sys.stderr)
    else:
        print(f"error: {message}", file=sys.stderr)
    return exit_code


def _print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
