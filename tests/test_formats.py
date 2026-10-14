from __future__ import annotations

import io
import json
import unittest
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path
from shutil import rmtree
from unittest.mock import patch
from uuid import uuid4

from jake_resume.cli import _normalize_formats, _parser, main


ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def workspace_tempdir():
    directory = ROOT / ".jake-resume-tmp" / f"test-formats-{uuid4().hex}"
    directory.mkdir(parents=True, exist_ok=False)
    try:
        yield directory
    finally:
        rmtree(directory, ignore_errors=True)


class FormatSelectionTests(unittest.TestCase):
    def test_short_render_flags(self) -> None:
        args = _parser().parse_args(
            [
                "render",
                "resume.json",
                "-f",
                "pdf,svg",
                "-o",
                "build/resume",
                "-e",
                "pdflatex",
                "-l",
                "source.tex",
                "-w",
                "error",
                "-c",
                "censorship.json",
            ]
        )
        self.assertEqual(args.format, ["pdf,svg"])
        self.assertEqual(args.output, Path("build/resume"))
        self.assertEqual(args.engine, "pdflatex")
        self.assertEqual(args.latex_output, Path("source.tex"))
        self.assertEqual(args.warnings, "error")
        self.assertEqual(args.censorship_file, Path("censorship.json"))

    def test_format_lists_aliases_duplicates_and_all(self) -> None:
        self.assertEqual(_normalize_formats(["pdf,svg", "pdf"]), ["pdf", "svg"])
        self.assertEqual(_normalize_formats(["tex", "pdf"]), ["latex", "pdf"])
        self.assertEqual(_normalize_formats(["all"]), ["latex", "pdf", "svg", "html"])

    def test_pdf_and_svg_share_one_pdf_compilation(self) -> None:
        with workspace_tempdir() as root:
            input_path = root / "resume.json"
            output_base = root / "resume"
            input_path.write_text(json.dumps({"basics": {"name": "Format Test"}}), encoding="utf-8")

            def fake_compile(_tex: str, output: str | Path, _engine: str = "pdflatex") -> Path:
                path = Path(output)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"%PDF-test")
                return path

            stdout = io.StringIO()
            with patch("jake_resume.cli.compile_pdf", side_effect=fake_compile) as compile_pdf, patch(
                "jake_resume.cli.load_pdf_pages", return_value=[object()]
            ) as load_pages, patch("jake_resume.cli.write_svg_pages") as write_svg, redirect_stdout(stdout):
                result = main(
                    [
                        "render",
                        str(input_path),
                        "--format",
                        "pdf,svg",
                        "--output",
                        str(output_base),
                    ]
                )

            self.assertEqual(result, 0)
            self.assertEqual(compile_pdf.call_count, 1)
            self.assertEqual(load_pages.call_count, 1)
            self.assertEqual(write_svg.call_count, 1)
            self.assertIn(str(root / "resume.pdf"), stdout.getvalue())
            self.assertIn(str(root / "resume-svg"), stdout.getvalue())

    def test_all_shares_one_pdf_and_one_page_conversion(self) -> None:
        with workspace_tempdir() as root:
            input_path = root / "resume.json"
            output_base = root / "resume"
            input_path.write_text(json.dumps({"basics": {"name": "Format Test"}}), encoding="utf-8")

            def fake_compile(_tex: str, output: str | Path, _engine: str = "pdflatex") -> Path:
                path = Path(output)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"%PDF-test")
                return path

            with patch("jake_resume.cli.compile_pdf", side_effect=fake_compile) as compile_pdf, patch(
                "jake_resume.cli.load_pdf_pages", return_value=[object()]
            ) as load_pages, patch("jake_resume.cli.write_svg_pages") as write_svg, patch(
                "jake_resume.cli.write_html_pages"
            ) as write_html:
                result = main(
                    [
                        "render",
                        str(input_path),
                        "--format",
                        "all",
                        "--output",
                        str(output_base),
                    ]
                )

            self.assertEqual(result, 0)
            self.assertEqual(compile_pdf.call_count, 1)
            self.assertEqual(load_pages.call_count, 1)
            self.assertEqual(write_svg.call_count, 1)
            self.assertEqual(write_html.call_count, 1)
            self.assertTrue((root / "resume.tex").exists())

    def test_repeated_format_flags_and_multi_format_latex_output(self) -> None:
        with workspace_tempdir() as root:
            input_path = root / "resume.json"
            input_path.write_text(json.dumps({"basics": {"name": "Format Test"}}), encoding="utf-8")

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                result = main(
                    [
                        "render",
                        str(input_path),
                        "--format",
                        "pdf",
                        "--format",
                        "svg",
                        "--output",
                        str(root / "resume"),
                        "--latex-output",
                        str(root / "debug.tex"),
                    ]
                )

            self.assertEqual(result, 1)
            self.assertIn("cannot be used with multiple formats", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
