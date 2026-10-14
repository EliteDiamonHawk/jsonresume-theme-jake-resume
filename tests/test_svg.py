from __future__ import annotations

import json
import unittest
from contextlib import contextmanager
from pathlib import Path
from shutil import rmtree
from unittest.mock import patch
from uuid import uuid4

import pymupdf

from jake_resume.cli import main
from jake_resume.render import render_html, render_svg
from jake_resume.svg import SvgRenderingError


ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def workspace_tempdir():
    directory = ROOT / ".jake-resume-tmp" / f"test-svg-{uuid4().hex}"
    directory.mkdir(parents=True, exist_ok=False)
    try:
        yield directory
    finally:
        rmtree(directory, ignore_errors=True)


def write_pdf(path: Path, pages: int = 1, with_link: bool = False) -> Path:
    document = pymupdf.open()
    for index in range(pages):
        page = document.new_page(width=612, height=792)
        page.insert_text((72, 72), f"Resume page {index + 1}")
        if with_link and index == 0:
            page.insert_link(
                {
                    "kind": pymupdf.LINK_URI,
                    "from": pymupdf.Rect(60, 50, 180, 90),
                    "uri": "https://example.com/profile",
                }
            )
    document.save(str(path))
    document.close()
    return path


def write_text_pdf(path: Path, text: str = "Resume page 1") -> Path:
    document = pymupdf.open()
    page = document.new_page(width=612, height=792)
    page.insert_text((72, 72), text)
    document.save(str(path))
    document.close()
    return path


class SvgRendererTests(unittest.TestCase):
    def test_render_svg_writes_one_file_per_pdf_page(self) -> None:
        with workspace_tempdir() as root:
            pdf = write_pdf(root / "resume.pdf", pages=2)
            output_dir = root / "svg"

            paths = render_svg(pdf, output_dir)

            self.assertEqual([path.name for path in paths], ["page-1.svg", "page-2.svg"])
            self.assertTrue(all(path.read_text(encoding="utf-8").lstrip().startswith("<svg") for path in paths))

    def test_render_html_embeds_pages_and_preserves_pdf_links(self) -> None:
        with workspace_tempdir() as root:
            pdf = write_pdf(root / "resume.pdf", pages=2, with_link=True)
            output = root / "resume.html"

            render_html(pdf, output)
            html = output.read_text(encoding="utf-8")

            self.assertEqual(html.count('class="resume-page"'), 2)
            self.assertGreaterEqual(html.count("<svg"), 2)
            self.assertIn("overflow-y: auto", html)
            self.assertIn('href="https://example.com/profile"', html)
            self.assertIn('class="pdf-link"', html)
            self.assertEqual(html.count('class="text-layer"'), 2)
            self.assertIn("Resume page 1", html)
            self.assertIn("z-index: 2", html)
            self.assertNotIn("<img", html.lower())

    def test_html_text_layer_escapes_text_and_can_be_disabled(self) -> None:
        with workspace_tempdir() as root:
            pdf = write_text_pdf(root / "resume.pdf", "A & <B>")
            enabled = root / "enabled.html"
            disabled = root / "disabled.html"

            render_html(pdf, enabled)
            render_html(pdf, disabled, selectable_text=False)

            enabled_html = enabled.read_text(encoding="utf-8")
            disabled_html = disabled.read_text(encoding="utf-8")
            self.assertIn("A &amp; &lt;B&gt;", enabled_html)
            self.assertNotIn("A & <B>", enabled_html)
            self.assertNotIn('class="text-layer"', disabled_html)
            self.assertIn("<svg", disabled_html)

    def test_invalid_and_empty_pdfs_raise_clear_errors(self) -> None:
        with workspace_tempdir() as root:
            invalid = root / "invalid.pdf"
            invalid.write_bytes(b"not a PDF")
            with self.assertRaises(SvgRenderingError):
                render_svg(invalid, root / "invalid-svg")

            empty = root / "empty.pdf"
            empty.write_bytes(b"placeholder")
            document = pymupdf.open()
            with patch("jake_resume.svg.pymupdf.open", return_value=document):
                with self.assertRaisesRegex(SvgRenderingError, "contains no pages"):
                    render_html(empty, root / "empty.html")

    def test_cli_svg_output_uses_a_directory(self) -> None:
        with workspace_tempdir() as root:
            input_path = root / "resume.json"
            output_dir = root / "resume-svg"
            input_path.write_text(json.dumps({"basics": {"name": "CLI Test"}}), encoding="utf-8")

            def fake_compile(_tex: str, output: str | Path, _engine: str = "pdflatex") -> Path:
                return write_pdf(Path(output), pages=2)

            with patch("jake_resume.cli.compile_pdf", side_effect=fake_compile):
                result = main(
                    [
                        "render",
                        str(input_path),
                        "--format",
                        "svg",
                        "--output",
                        str(output_dir),
                    ]
                )

            self.assertEqual(result, 0)
            self.assertTrue((output_dir / "page-1.svg").exists())
            self.assertTrue((output_dir / "page-2.svg").exists())

    def test_cli_svg_censorship_output_uses_variant_directories(self) -> None:
        with workspace_tempdir() as root:
            input_path = root / "resume.json"
            censorship_path = root / "censorship.json"
            output_dir = root / "build"
            input_path.write_text(json.dumps({"basics": {"name": "CLI Test", "email": "a@example.com"}}), encoding="utf-8")
            censorship_path.write_text(json.dumps({"remove": ["basics.email"]}), encoding="utf-8")

            def fake_compile(_tex: str, output: str | Path, _engine: str = "pdflatex") -> Path:
                return write_pdf(Path(output), pages=2)

            with patch("jake_resume.cli.compile_pdf", side_effect=fake_compile):
                result = main(
                    [
                        "render",
                        str(input_path),
                        "--format",
                        "svg",
                        "--output-dir",
                        str(output_dir),
                        "--censorship-file",
                        str(censorship_path),
                    ]
                )

            self.assertEqual(result, 0)
            self.assertTrue((output_dir / "resume" / "resume-svg" / "page-1.svg").exists())
            self.assertTrue((output_dir / "resume-censored" / "resume-censored-svg" / "page-2.svg").exists())


if __name__ == "__main__":
    unittest.main()
