from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from local_first_checklist.core import Checklist


class ChecklistTests(unittest.TestCase):
    def test_add_persists_item(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tasks.json"
            checklist = Checklist(path)

            item = checklist.add("Write docs")

            reloaded = Checklist(path)
            self.assertEqual(item.id, 1)
            self.assertEqual(reloaded.list()[0].title, "Write docs")

    def test_complete_hides_item_from_default_list(self) -> None:
        with TemporaryDirectory() as directory:
            checklist = Checklist(Path(directory) / "tasks.json")
            item = checklist.add("Validate code")

            checklist.complete(item.id)

            self.assertEqual(checklist.list(), [])
            self.assertTrue(checklist.list(include_done=True)[0].done)

    def test_empty_title_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            checklist = Checklist(Path(directory) / "tasks.json")

            with self.assertRaises(ValueError):
                checklist.add("   ")


if __name__ == "__main__":
    unittest.main()

