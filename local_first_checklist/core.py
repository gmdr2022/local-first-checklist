from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path


@dataclass(frozen=True)
class ChecklistItem:
    id: int
    title: str
    done: bool = False
    created_at: str = ""
    completed_at: str | None = None


class Checklist:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.items = self._load()

    def add(self, title: str) -> ChecklistItem:
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("title must not be empty")

        item = ChecklistItem(
            id=self._next_id(),
            title=clean_title,
            created_at=_now_iso(),
        )
        self.items.append(item)
        self._save()
        return item

    def complete(self, item_id: int) -> ChecklistItem:
        for index, item in enumerate(self.items):
            if item.id == item_id:
                if item.done:
                    return item
                completed = ChecklistItem(
                    id=item.id,
                    title=item.title,
                    done=True,
                    created_at=item.created_at,
                    completed_at=_now_iso(),
                )
                self.items[index] = completed
                self._save()
                return completed
        raise KeyError(f"item not found: {item_id}")

    def list(self, include_done: bool = False) -> list[ChecklistItem]:
        if include_done:
            return list(self.items)
        return [item for item in self.items if not item.done]

    def _next_id(self) -> int:
        if not self.items:
            return 1
        return max(item.id for item in self.items) + 1

    def _load(self) -> list[ChecklistItem]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("checklist data must be a list")
        return [ChecklistItem(**item) for item in data]

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(item) for item in self.items]
        self.path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def default_data_path() -> Path:
    return Path.home() / ".local-first-checklist" / "tasks.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

