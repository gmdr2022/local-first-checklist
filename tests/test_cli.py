from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from local_first_checklist.cli import main


class CliTests(unittest.TestCase):
    def run_cli(self, *arguments: str) -> tuple[int, str, str]:
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(list(arguments))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_json_command_lifecycle(self) -> None:
        with TemporaryDirectory() as directory:
            path = str(Path(directory) / "tasks.json")
            code, output, error = self.run_cli("--data", path, "--json", "add", "Ship v1")
            self.assertEqual((code, error), (0, ""))
            self.assertEqual(json.loads(output)["action"], "added")

            self.assertEqual(self.run_cli("--data", path, "done", "1")[0], 0)
            self.assertEqual(self.run_cli("--data", path, "reopen", "1")[0], 0)
            self.assertEqual(self.run_cli("--data", path, "edit", "1", "Ship v1.0")[0], 0)

            code, output, _ = self.run_cli("--data", path, "--json", "list", "--all")
            payload = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(payload["items"][0]["title"], "Ship v1.0")

    def test_destructive_commands_require_yes(self) -> None:
        with TemporaryDirectory() as directory:
            path = str(Path(directory) / "tasks.json")
            self.run_cli("--data", path, "add", "Keep")
            code, _, error = self.run_cli("--data", path, "remove", "1")
            self.assertEqual(code, 2)
            self.assertIn("requires --yes", error)
            self.assertEqual(self.run_cli("--data", path, "list")[0], 0)

    def test_doctor_does_not_modify_invalid_data(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "tasks.json"
            path.write_text("{broken", encoding="utf-8")
            before = path.read_bytes()

            code, output, _ = self.run_cli("--data", str(path), "--json", "doctor")

            self.assertEqual(code, 1)
            self.assertEqual(json.loads(output)["primary"]["status"], "invalid")
            self.assertEqual(path.read_bytes(), before)

    def test_recover_requires_yes_and_returns_json(self) -> None:
        with TemporaryDirectory() as directory:
            path = str(Path(directory) / "tasks.json")
            self.run_cli("--data", path, "add", "First")
            self.run_cli("--data", path, "edit", "1", "Second")
            Path(path).write_text("broken", encoding="utf-8")

            self.assertEqual(self.run_cli("--data", path, "recover")[0], 2)
            code, output, _ = self.run_cli("--data", path, "--json", "recover", "--yes")
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output)["action"], "recovered")

    def test_domain_errors_use_exit_one(self) -> None:
        with TemporaryDirectory() as directory:
            path = str(Path(directory) / "tasks.json")
            code, _, error = self.run_cli("--data", path, "--json", "done", "99")
            self.assertEqual(code, 1)
            self.assertEqual(json.loads(error)["exit_code"], 1)


if __name__ == "__main__":
    unittest.main()
