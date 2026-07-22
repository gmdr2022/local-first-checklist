from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from local_first_checklist.core import (
    Checklist,
    DataValidationError,
    RecoveryError,
    backup_path_for,
)


class ChecklistTests(unittest.TestCase):
    def test_add_persists_versioned_schema_and_unicode(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "tasks.json"

            item = Checklist(path).add("Revisar operação — manhã")

            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(payload["items"][0]["title"], item.title)
            self.assertEqual(Checklist(path).list()[0], item)

    def test_legacy_list_is_migrated_only_on_successful_mutation(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tasks.json"
            legacy = [
                {
                    "id": 1,
                    "title": "Existing task",
                    "done": False,
                    "created_at": "2026-01-01T10:00:00+00:00",
                    "completed_at": None,
                }
            ]
            original = (json.dumps(legacy, indent=2) + "\n").encode()
            path.write_bytes(original)

            checklist = Checklist(path)
            self.assertTrue(checklist.loaded_legacy_format)
            self.assertEqual(path.read_bytes(), original)

            checklist.add("New task")

            self.assertEqual(backup_path_for(path).read_bytes(), original)
            self.assertEqual(json.loads(path.read_text())["schema_version"], 1)

    def test_complete_reopen_edit_and_remove(self) -> None:
        with TemporaryDirectory() as directory:
            checklist = Checklist(Path(directory) / "tasks.json")
            item = checklist.add("Draft")

            completed = checklist.complete(item.id)
            self.assertTrue(completed.done)
            self.assertIsNotNone(completed.completed_at)
            self.assertEqual(checklist.list(), [])

            reopened = checklist.reopen(item.id)
            self.assertFalse(reopened.done)
            self.assertIsNone(reopened.completed_at)
            self.assertEqual(checklist.edit(item.id, "Final").title, "Final")
            self.assertEqual(checklist.remove(item.id).title, "Final")
            self.assertEqual(checklist.list(include_done=True), [])

    def test_empty_title_is_rejected_without_writing(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tasks.json"
            with self.assertRaises(DataValidationError):
                Checklist(path).add("   ")
            self.assertFalse(path.exists())

    def test_duplicate_ids_are_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tasks.json"
            item = {
                "id": 1,
                "title": "One",
                "done": False,
                "created_at": "2026-01-01T10:00:00+00:00",
                "completed_at": None,
            }
            path.write_text(
                json.dumps({"schema_version": 1, "items": [item, item]}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(DataValidationError, "duplicate item id"):
                Checklist(path)

    def test_unknown_schema_and_invalid_timestamps_fail_closed(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tasks.json"
            path.write_text(json.dumps({"schema_version": 2, "items": []}), encoding="utf-8")
            with self.assertRaisesRegex(DataValidationError, "unsupported schema_version"):
                Checklist(path)

            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "items": [
                            {
                                "id": 1,
                                "title": "No timezone",
                                "done": False,
                                "created_at": "2026-01-01T10:00:00",
                                "completed_at": None,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(DataValidationError, "UTC offset"):
                Checklist(path)

    def test_interrupted_primary_replace_leaves_previous_primary_intact(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tasks.json"
            checklist = Checklist(path)
            checklist.add("Stable")
            original = path.read_bytes()
            real_replace = os.replace

            def fail_primary(source: object, destination: object) -> None:
                if Path(destination) == path:
                    raise OSError("simulated interruption")
                real_replace(source, destination)

            with mock.patch("local_first_checklist.core.os.replace", side_effect=fail_primary):
                with self.assertRaisesRegex(OSError, "simulated interruption"):
                    checklist.add("Interrupted")

            self.assertEqual(path.read_bytes(), original)
            self.assertEqual([item.title for item in checklist.list()], ["Stable"])
            self.assertEqual(Checklist(path).list()[0].title, "Stable")
            self.assertEqual(list(path.parent.glob("*.tmp")), [])

    def test_doctor_reports_corruption_and_recovery_is_explicit(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tasks.json"
            checklist = Checklist(path)
            checklist.add("Version one")
            checklist.edit(1, "Version two")
            path.write_text("{broken", encoding="utf-8")

            report = Checklist.diagnose(path)
            self.assertFalse(report.healthy)
            self.assertEqual(report.primary.status, "invalid")
            self.assertEqual(report.backup.status, "ok")

            recovered = Checklist.recover(path)
            self.assertTrue(recovered.healthy)
            self.assertEqual(Checklist(path).list()[0].title, "Version one")

    def test_recovery_requires_a_valid_backup(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tasks.json"
            with self.assertRaisesRegex(RecoveryError, "backup not found"):
                Checklist.recover(path)

            backup_path_for(path).write_text("not json", encoding="utf-8")
            with self.assertRaises(DataValidationError):
                Checklist.recover(path)
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
