from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from jake_resume.adapters import normalize
from jake_resume.render import CompilationError, _create_scratch_root, compile_pdf
from jake_resume.latex import render_latex as render_tex


ROOT = Path(__file__).resolve().parents[1]


class RendererTests(unittest.TestCase):
    def test_scratch_root_prefers_system_temp_directory(self) -> None:
        expected = Path("C:/system-temp/jake-resume-test")
        with patch("jake_resume.render.tempfile.gettempdir", return_value="C:/system-temp"), patch(
            "jake_resume.render._new_scratch_root", return_value=expected
        ) as new_scratch_root, patch("jake_resume.render._scratch_root_is_writable", return_value=True):
            scratch_root = _create_scratch_root()

        self.assertEqual(scratch_root, expected)
        new_scratch_root.assert_called_once_with(Path("C:/system-temp"))

    def test_scratch_root_falls_back_to_current_directory(self) -> None:
        fallback = ROOT / ".jake-resume-tmp" / "jake-resume-test"
        with patch(
            "jake_resume.render._new_scratch_root", side_effect=[OSError("system temp unavailable"), fallback]
        ) as new_scratch_root, patch("jake_resume.render._scratch_root_is_writable", return_value=True):
            scratch_root = _create_scratch_root()

        self.assertEqual(scratch_root, fallback)
        self.assertEqual(new_scratch_root.call_count, 2)
        self.assertEqual(new_scratch_root.call_args_list[1].args[0], ROOT / ".jake-resume-tmp")

    def test_json_resume_creates_input_sections_and_preserves_unknown_fields(self) -> None:
        data = json.loads((ROOT / "examples" / "jsonresume.json").read_text(encoding="utf-8"))
        resume = normalize(data)
        tex = render_tex(resume)
        self.assertIn(r"\resumeSection{Research}", tex)
        self.assertIn(r"\resumeSection{Work}", tex)
        self.assertIn(r"\resumeSection{Community}", tex)
        self.assertIn("Improved chart comprehension", tex)
        self.assertNotIn(r"\resumeSection{Education}", tex)

    def test_rxresume_layout_and_custom_sections(self) -> None:
        data = json.loads((ROOT / "examples" / "rxresume-v5.json").read_text(encoding="utf-8"))
        resume = normalize(data)
        self.assertEqual([section.title for section in resume.sections], ["Profile", "Selected Experience", "Community Work", "Research"])
        tex = render_tex(resume)
        self.assertIn(r"\resumeSection{Profile}", tex)
        self.assertIn(r"\resumeSection{Selected Experience}", tex)
        self.assertIn(r"\resumeSection{Community Work}", tex)
        self.assertIn(r"\resumeSection{Research}", tex)
        self.assertIn(r"\textbf{reliable systems}", tex)

    def test_rxresume_metadata_profiles_dates_and_internal_fields(self) -> None:
        data = {
            "basics": {"name": "Profile Test"},
            "sections": {
                "profiles": {
                    "title": "Profiles",
                    "items": [
                        {
                            "id": "internal-id",
                            "icon": "github-logo",
                            "iconColor": "blue",
                            "network": "GitHub",
                            "username": "example",
                            "website": {
                                "url": "https://github.com/example",
                                "label": "example",
                                "inlineLink": True,
                            },
                        }
                    ],
                },
                "experience": {
                    "title": "Experience",
                    "items": [
                        {
                            "name": "Example",
                            "dates": {"start": "2024", "present": True},
                            "id": "hidden-id",
                            "icon": "briefcase",
                        }
                    ],
                },
            },
            "metadata": {
                "layout": {"pages": [{"main": ["profiles", "experience"], "sidebar": []}]},
                "page": {"format": "a4", "marginX": 14, "marginY": 12, "hideLinkUnderline": True},
                "design": {"colors": {"primary": "rgba(0, 132, 209, 1)"}},
            },
        }
        tex = render_tex(normalize(data))
        self.assertIn(r"\documentclass[letterpaper,11pt]{article}", tex)
        self.assertNotIn("a4paper", tex)
        self.assertNotIn("geometry", tex)
        self.assertIn(r"\resumeLink{https://github.com/example}{GitHub}", tex)
        self.assertIn("2024 -- Present", tex)
        self.assertNotIn("internal-id", tex)
        self.assertNotIn("briefcase", tex)
        self.assertNotIn(r"\resumeSection{Profiles}", tex)

    def test_dynamic_date_shapes_and_user_fields(self) -> None:
        data = {
            "basics": {"name": "Date Test"},
            "sections": {
                "custom": {
                    "title": "Custom Work",
                    "items": [
                        {
                            "name": "Example",
                            "period": {"start": "2024-06", "present": True},
                            "location": {"city": "Oakland", "region": "CA"},
                            "description": ["One result"],
                            "id": "hidden",
                        },
                        {"title": "Other", "dates": {"start": "January 2023", "end": "March 2024"}},
                    ],
                }
            },
        }
        tex = render_tex(normalize(data, "rxresume-v5"))
        self.assertIn("Jun. 2024 -- Present", tex)
        self.assertIn("Jan. 2023 -- Mar. 2024", tex)
        self.assertIn("Oakland, CA", tex)
        self.assertIn("One result", tex)
        self.assertNotIn("hidden", tex)

    def test_grade_text_is_not_bolded(self) -> None:
        resume = normalize(
            {
                "basics": {"name": "Grade Test"},
                "education": [{"institution": "Example University", "grade": "GPA 3.8 since Spring 2026"}],
            }
        )
        tex = render_tex(resume)
        self.assertIn("GPA 3.8 since Spring 2026", tex)
        self.assertNotIn(r"\textbf{GPA}", tex)

    def test_tex_escaping_and_links(self) -> None:
        resume = normalize({"basics": {"name": "A & B", "email": "a_b@example.com"}, "notes": [{"value": "50% complete #1"}]})
        tex = render_tex(resume)
        self.assertIn(r"A \& B", tex)
        self.assertIn(r"50\% complete \#1", tex)
        self.assertIn(r"mailto:a_b@example.com", tex)
        self.assertIn(r"\resumeLink{mailto:a_b@example.com}", tex)

    def test_engine_specific_preamble_guards(self) -> None:
        tex = render_tex(normalize({"basics": {"name": "Engine Test"}}))

        pdftex_start = tex.index(r"\ifPDFTeX")
        glyph_mapping = tex.index(r"\input{glyphtounicode}")
        pdftex_end = tex.index(r"\fi", glyph_mapping)
        self.assertLess(pdftex_start, glyph_mapping)
        self.assertLess(glyph_mapping, pdftex_end)

        unicode_start = tex.index(r"\ifXeTeX")
        self.assertLess(unicode_start, tex.index(r"\usepackage{xeCJK}"))
        self.assertLess(unicode_start, tex.index(r"\setCJKmainfont{Noto Serif CJK JP}"))
        self.assertIn(r"\usepackage{luatexja-fontspec}", tex)

        unicode_mapping = tex.index(r"\pdfgentounicode=1")
        self.assertGreater(tex.rfind(r"\ifPDFTeX", 0, unicode_mapping), pdftex_end)
        self.assertLess(unicode_mapping, tex.index(r"\fi", unicode_mapping))

    def _assert_cjk_compiles(self, engine: str) -> None:
        if shutil.which(engine) is None:
            self.skipTest(f"{engine} is not installed")

        resume = normalize({"basics": {"name": "日本語"}, "notes": [{"value": "中文 한국어"}]})
        output = ROOT / f".jake-resume-{engine}-test.pdf"
        try:
            try:
                compile_pdf(render_tex(resume), output, engine)
            except CompilationError as exc:
                message = str(exc).lower()
                unavailable = (
                    "fontspec.sty" in message
                    or "xecjk.sty" in message
                    or "luatexja-fontspec.sty" in message
                    or "noto serif cjk jp" in message
                    or "font-not-found" in message
                    or "access is denied" in message
                    or "fontconfig initialization failed" in message
                    or "windows api error 5" in message
                )
                if unavailable:
                    self.skipTest(f"{engine} CJK dependencies are unavailable: {exc}")
                raise
            self.assertTrue(output.exists())
            self.assertTrue(output.read_bytes().startswith(b"%PDF"))
        finally:
            output.unlink(missing_ok=True)

    def test_pdf_compiles_with_xelatex_and_cjk_text_when_available(self) -> None:
        self._assert_cjk_compiles("xelatex")

    def test_pdf_compiles_with_lualatex_and_cjk_text_when_available(self) -> None:
        self._assert_cjk_compiles("lualatex")

    def test_pdf_compiles_when_pdflatex_is_available(self) -> None:
        if shutil.which("pdflatex") is None:
            self.skipTest("pdflatex is not installed")
        resume = normalize({"basics": {"name": "Compile Test", "email": "compile@example.com"}, "notes": [{"value": "PDF output"}]})
        output = ROOT / ".jake-resume-test.pdf"
        try:
            try:
                output = compile_pdf(render_tex(resume), output)
            except CompilationError as exc:
                if "Access is denied" in str(exc) or "font" in str(exc).lower():
                    self.skipTest(f"local MiKTeX installation cannot write its font cache: {exc}")
                raise
            self.assertTrue(output.exists())
            pdf_bytes = output.read_bytes()
            self.assertTrue(pdf_bytes.startswith(b"%PDF"))
            self.assertIn(b"/URI", pdf_bytes)
        finally:
            output.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
