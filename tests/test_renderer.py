from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path

from jake_resume.adapters import normalize
from jake_resume.render import CompilationError, compile_pdf
from jake_resume.latex import render_latex as render_tex


ROOT = Path(__file__).resolve().parents[1]


class RendererTests(unittest.TestCase):
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
