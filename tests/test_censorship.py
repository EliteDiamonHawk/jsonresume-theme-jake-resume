from __future__ import annotations

import io
import json
import unittest
from contextlib import contextmanager, redirect_stdout
from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from jake_resume.censorship import CensorshipError, apply_censorship, load_censorship_file
from jake_resume.cli import main
from jake_resume.latex import render_latex as render_tex
from jake_resume.adapters import normalize


ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def workspace_tempdir():
    directory = ROOT / ".jake-resume-tmp" / f"test-censorship-{uuid4().hex}"
    directory.mkdir(parents=True, exist_ok=False)
    try:
        yield directory
    finally:
        rmtree(directory, ignore_errors=True)


class CensorshipTests(unittest.TestCase):
    def test_removes_nested_values_without_mutating_source(self) -> None:
        source = {
            "basics": {"email": "alex@example.com", "phone": "555-0100"},
            "sections": {"experience": {"items": [{"location": "Oakland", "name": "Example"}]}},
        }

        censored, diagnostics = apply_censorship(
            source,
            ["basics.email", "basics.phone", "sections.experience.items.0.location"],
        )

        self.assertEqual(diagnostics, [])
        self.assertEqual(source["basics"]["email"], "alex@example.com")
        self.assertEqual(source["sections"]["experience"]["items"][0]["location"], "Oakland")
        self.assertNotIn("email", censored["basics"])
        self.assertNotIn("phone", censored["basics"])
        self.assertNotIn("location", censored["sections"]["experience"]["items"][0])

    def test_missing_paths_warn_and_render_without_removed_contact_data(self) -> None:
        data = {"basics": {"name": "Alex Morgan", "email": "alex@example.com", "phone": "555-0100"}}
        censored, diagnostics = apply_censorship(data, ["basics.email", "basics.phone", "basics.missing"])
        resume = normalize(censored)
        resume.diagnostics.extend(diagnostics)
        tex = render_tex(resume)

        self.assertEqual(len(resume.warnings), 1)
        self.assertIn("basics.missing", str(resume.warnings[0]))
        self.assertNotIn("alex@example.com", tex)
        self.assertNotIn("555-0100", tex)
        self.assertNotIn("mailto:", tex)
        self.assertNotIn("tel:", tex)

    def test_rxresume_nested_path_is_removed(self) -> None:
        data = {
            "basics": {"name": "Alex Morgan"},
            "sections": {
                "experience": {
                    "items": [{"name": "Example Labs", "location": "Oakland"}]
                }
            },
        }
        censored, diagnostics = apply_censorship(data, ["sections.experience.items.0.location"])
        resume = normalize(censored, "rxresume-v5")
        resume.diagnostics.extend(diagnostics)

        self.assertEqual(resume.warnings, [])
        self.assertNotIn("location", resume.sections[0].items[0])

    def test_censorship_file_validation(self) -> None:
        with workspace_tempdir() as directory:
            path = directory / "censorship.json"
            path.write_text(json.dumps({"remove": ["basics.email"]}), encoding="utf-8")
            self.assertEqual(load_censorship_file(path), ["basics.email"])

            path.write_text(json.dumps({"remove": [""]}), encoding="utf-8")
            with self.assertRaises(CensorshipError):
                load_censorship_file(path)

            path.write_text(json.dumps({"remove": ["basics.*"]}), encoding="utf-8")
            with self.assertRaises(CensorshipError):
                load_censorship_file(path)

    def test_cli_censored_only_output(self) -> None:
        with workspace_tempdir() as root:
            input_path = root / "resume.json"
            censorship_path = root / "censorship.json"
            output_path = root / "resume-censored.tex"
            input_path.write_text(
                json.dumps({"basics": {"name": "Alex", "email": "alex@example.com", "phone": "555-0100"}}),
                encoding="utf-8",
            )
            censorship_path.write_text(json.dumps({"remove": ["basics.email", "basics.phone"]}), encoding="utf-8")

            result = main(
                [
                    "render",
                    str(input_path),
                    "--format",
                    "latex",
                    "--output",
                    str(output_path),
                    "--censorship-file",
                    str(censorship_path),
                ]
            )

            self.assertEqual(result, 0)
            tex = output_path.read_text(encoding="utf-8")
            self.assertNotIn("alex@example.com", tex)
            self.assertNotIn("555-0100", tex)

    def test_cli_dual_output(self) -> None:
        with workspace_tempdir() as root:
            input_path = root / "resume.json"
            censorship_path = root / "censorship.json"
            output_dir = root / "build"
            input_path.write_text(
                json.dumps({"basics": {"name": "Alex", "email": "alex@example.com"}}),
                encoding="utf-8",
            )
            censorship_path.write_text(json.dumps({"remove": ["basics.email"]}), encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "render",
                        str(input_path),
                        "--format",
                        "tex",
                        "--output-dir",
                        str(output_dir),
                        "--censorship-file",
                        str(censorship_path),
                    ]
                )

            self.assertEqual(result, 0)
            self.assertIn("resume.tex", stdout.getvalue())
            self.assertTrue((output_dir / "resume" / "resume.tex").exists())
            censored = (output_dir / "resume-censored" / "resume-censored.tex").read_text(encoding="utf-8")
            uncensored = (output_dir / "resume" / "resume.tex").read_text(encoding="utf-8")
            self.assertNotIn("alex@example.com", censored)
            self.assertIn("alex@example.com", uncensored)


if __name__ == "__main__":
    unittest.main()
