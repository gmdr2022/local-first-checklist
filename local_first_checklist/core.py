from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import Any


SCHEMA_VERSION = 1


class ChecklistError(Exception):
    """Base class for errors that can be presented safely to CLI users."""


class DataValidationError(ChecklistError):
    """Raised when persisted checklist data does not satisfy the schema."""


class ItemNotFoundError(ChecklistError):
    """Raised when an operation references an unknown item id."""


class RecoveryError(ChecklistError):
    """Raised when a requested recovery cannot be completed safely."""


@dataclass(frozen=True)
class ChecklistItem:
    id: int
    title: str
    done: bool = False
    created_at: str = ""
    completed_at: str | None = None


@dataclass(frozen=True)
class FileHealth:
    path: str
    status: str
    schema_version: int | None = None
    item_count: int | None = None
    detail: str | None = None

    @property
    def healthy(self) -> bool:
        return self.status in {"missing", "ok", "legacy"}

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DiagnosticReport:
    primary: FileHealth
    backup: FileHealth

    @property
    def healthy(self) -> bool:
        return self.primary.healthy and self.backup.healthy

    def to_dict(self) -> dict[str, object]:
        return {
            "healthy": self.healthy,
            "primary": self.primary.to_dict(),
            "backup": self.backup.to_dict(),
        }


class Checklist:
    def __init__(self, path: Path) -> None:
        self.path = path.expanduser()
        self.items, self.loaded_legacy_format = _load_items(self.path)

    @property
    def backup_path(self) -> Path:
        return backup_path_for(self.path)

    def add(self, title: str) -> ChecklistItem:
        item = ChecklistItem(
            id=self._next_id(),
            title=_clean_title(title),
            created_at=_now_iso(),
        )
        self._save([*self.items, item])
        return item

    def complete(self, item_id: int) -> ChecklistItem:
        index, item = self._find(item_id)
        if item.done:
            return item
        completed = replace(item, done=True, completed_at=_now_iso())
        updated = list(self.items)
        updated[index] = completed
        self._save(updated)
        return completed

    def reopen(self, item_id: int) -> ChecklistItem:
        index, item = self._find(item_id)
        if not item.done:
            return item
        reopened = replace(item, done=False, completed_at=None)
        updated = list(self.items)
        updated[index] = reopened
        self._save(updated)
        return reopened

    def edit(self, item_id: int, title: str) -> ChecklistItem:
        index, item = self._find(item_id)
        edited = replace(item, title=_clean_title(title))
        updated = list(self.items)
        updated[index] = edited
        self._save(updated)
        return edited

    def remove(self, item_id: int) -> ChecklistItem:
        index, item = self._find(item_id)
        updated = list(self.items)
        del updated[index]
        self._save(updated)
        return item

    def list(self, include_done: bool = False) -> list[ChecklistItem]:
        if include_done:
            return list(self.items)
        return [item for item in self.items if not item.done]

    def _find(self, item_id: int) -> tuple[int, ChecklistItem]:
        if isinstance(item_id, bool) or not isinstance(item_id, int) or item_id <= 0:
            raise ItemNotFoundError(f"item not found: {item_id}")
        for index, item in enumerate(self.items):
            if item.id == item_id:
                return index, item
        raise ItemNotFoundError(f"item not found: {item_id}")

    def _next_id(self) -> int:
        if not self.items:
            return 1
        return max(item.id for item in self.items) + 1

    def _save(self, items: list[ChecklistItem]) -> None:
        validated = _validate_items([asdict(item) for item in items])
        payload = {
            "schema_version": SCHEMA_VERSION,
            "items": [asdict(item) for item in validated],
        }
        encoded = (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")

        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            # Only a validated primary is promoted to last-known-good backup.
            _load_items(self.path)
            _atomic_write_bytes(self.backup_path, self.path.read_bytes())
        _atomic_write_bytes(self.path, encoded)
        self.items = validated
        self.loaded_legacy_format = False

    @classmethod
    def diagnose(cls, path: Path) -> DiagnosticReport:
        primary = path.expanduser()
        return DiagnosticReport(
            primary=_inspect_file(primary),
            backup=_inspect_file(backup_path_for(primary)),
        )

    @classmethod
    def recover(cls, path: Path) -> DiagnosticReport:
        primary = path.expanduser()
        backup = backup_path_for(primary)
        if not backup.exists():
            raise RecoveryError(f"backup not found: {backup}")
        _load_items(backup)
        primary.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_bytes(primary, backup.read_bytes())
        return cls.diagnose(primary)


def backup_path_for(path: Path) -> Path:
    return path.with_name(f"{path.name}.bak")


def default_data_path() -> Path:
    return Path.home() / ".local-first-checklist" / "tasks.json"


def item_to_dict(item: ChecklistItem) -> dict[str, object]:
    return asdict(item)


def _clean_title(title: str) -> str:
    if not isinstance(title, str):
        raise DataValidationError("title must be a string")
    clean_title = title.strip()
    if not clean_title:
        raise DataValidationError("title must not be empty")
    return clean_title


def _load_items(path: Path) -> tuple[list[ChecklistItem], bool]:
    if not path.exists():
        return [], False
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise DataValidationError(f"cannot read data file: {exc}") from exc
    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DataValidationError(
            f"invalid JSON at line {exc.lineno}, column {exc.colno}"
        ) from exc

    if isinstance(data, list):
        return _validate_items(data), True
    if not isinstance(data, dict):
        raise DataValidationError("checklist data must be an object")
    if set(data) != {"schema_version", "items"}:
        raise DataValidationError("data object must contain only schema_version and items")
    if data["schema_version"] != SCHEMA_VERSION:
        raise DataValidationError(
            f"unsupported schema_version: {data['schema_version']!r}"
        )
    return _validate_items(data["items"]), False


def _validate_items(raw_items: object) -> list[ChecklistItem]:
    if not isinstance(raw_items, list):
        raise DataValidationError("items must be a list")

    items: list[ChecklistItem] = []
    seen_ids: set[int] = set()
    allowed = {"id", "title", "done", "created_at", "completed_at"}
    required = {"id", "title", "done", "created_at"}

    for index, raw_item in enumerate(raw_items):
        label = f"items[{index}]"
        if not isinstance(raw_item, dict):
            raise DataValidationError(f"{label} must be an object")
        keys = set(raw_item)
        if not required.issubset(keys) or not keys.issubset(allowed):
            raise DataValidationError(f"{label} has invalid or missing fields")

        item_id = raw_item["id"]
        if isinstance(item_id, bool) or not isinstance(item_id, int) or item_id <= 0:
            raise DataValidationError(f"{label}.id must be a positive integer")
        if item_id in seen_ids:
            raise DataValidationError(f"duplicate item id: {item_id}")
        seen_ids.add(item_id)

        title = raw_item["title"]
        if not isinstance(title, str) or not title.strip() or title != title.strip():
            raise DataValidationError(f"{label}.title must be a trimmed non-empty string")

        done = raw_item["done"]
        if not isinstance(done, bool):
            raise DataValidationError(f"{label}.done must be a boolean")

        created_at = raw_item["created_at"]
        _validate_timestamp(created_at, f"{label}.created_at")
        completed_at = raw_item.get("completed_at")
        if done:
            _validate_timestamp(completed_at, f"{label}.completed_at")
        elif completed_at is not None:
            raise DataValidationError(f"{label}.completed_at must be null while open")

        items.append(
            ChecklistItem(
                id=item_id,
                title=title,
                done=done,
                created_at=created_at,
                completed_at=completed_at,
            )
        )
    return items


def _validate_timestamp(value: object, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise DataValidationError(f"{label} must be an ISO 8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DataValidationError(f"{label} must be an ISO 8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DataValidationError(f"{label} must include a UTC offset")


def _inspect_file(path: Path) -> FileHealth:
    if not path.exists():
        return FileHealth(path=str(path), status="missing")
    try:
        items, legacy = _load_items(path)
    except DataValidationError as exc:
        return FileHealth(path=str(path), status="invalid", detail=str(exc))
    return FileHealth(
        path=str(path),
        status="legacy" if legacy else "ok",
        schema_version=None if legacy else SCHEMA_VERSION,
        item_count=len(items),
    )


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        _fsync_directory(path.parent)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
