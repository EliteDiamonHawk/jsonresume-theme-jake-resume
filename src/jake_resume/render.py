from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any

from .adapters import normalize
from .model import NormalizedResume
from .latex import render_latex as _render_latex
from .svg import (
    PageSvg,
    load_pdf_pages as _load_pdf_pages,
    render_html as _render_html,
    render_svg as _render_svg,
    write_html_pages as _write_html_pages,
    write_svg_pages as _write_svg_pages,
)


class CompilationError(RuntimeError):
    pass


def render_latex(resume: NormalizedResume) -> str:
    return _render_latex(resume)


# Compatibility for callers of the original Python API.  The generated file
# still uses the conventional .tex extension, but the format is LaTeX.
render_tex = render_latex


def _create_scratch_root() -> Path:
    """Create a private compiler workspace, preferring the system temp directory."""

    try:
        scratch_root = _new_scratch_root(Path(tempfile.gettempdir()))
        if _scratch_root_is_writable(scratch_root):
            return scratch_root
        shutil.rmtree(scratch_root, ignore_errors=True)
    except OSError:
        pass

    fallback_root = Path.cwd() / ".jake-resume-tmp"
    fallback_root.mkdir(parents=True, exist_ok=True)
    scratch_root = _new_scratch_root(fallback_root)
    if not _scratch_root_is_writable(scratch_root):
        shutil.rmtree(scratch_root, ignore_errors=True)
        raise OSError(f"Unable to create a writable compiler workspace in {fallback_root}")
    return scratch_root


def _new_scratch_root(parent: Path) -> Path:
    scratch_root = parent / f"jake-resume-{uuid.uuid4().hex}"
    scratch_root.mkdir()
    return scratch_root


def _scratch_root_is_writable(scratch_root: Path) -> bool:
    probe = scratch_root / ".write-test"
    try:
        probe.write_bytes(b"")
        probe.unlink()
        return True
    except OSError:
        return False


def compile_pdf(tex: str, output_path: str | Path, engine: str = "pdflatex") -> Path:
    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which(engine) is None:
        raise CompilationError(f"LaTeX compiler not found: {engine}")
    scratch_root = _create_scratch_root()
    stem = f"resume-{uuid.uuid4().hex}"
    tex_path = scratch_root / f"{stem}.tex"
    tex_path.write_text(tex, encoding="utf-8")
    try:
        miktex_root = scratch_root / f"{stem}-miktex"
        for name in ("config", "data", "cache"):
            (miktex_root / name).mkdir(parents=True, exist_ok=True)
        environment = os.environ.copy()
        environment.update(
            {
                "MIKTEX_USERCONFIG": str(miktex_root / "config"),
                "MIKTEX_USERDATA": str(miktex_root / "data"),
                "MIKTEX_USERCACHE": str(miktex_root / "cache"),
            }
        )
        command = [engine, "-interaction=nonstopmode", "-halt-on-error", tex_path.name]
        result = subprocess.run(command, cwd=scratch_root, text=True, capture_output=True, env=environment)
        pdf = scratch_root / f"{stem}.pdf"
        log = (result.stdout + "\n" + result.stderr).strip()
        if result.returncode != 0 and not (pdf.exists() and "Output written on" in log):
            raise CompilationError(f"{engine} failed with exit code {result.returncode}:\n{log[-6000:]}")
        if not pdf.exists():
            raise CompilationError(f"{engine} completed without producing a PDF.")
        output.write_bytes(pdf.read_bytes())
    finally:
        shutil.rmtree(scratch_root, ignore_errors=True)
    return output


def render_svg(pdf_path: str | Path, output_dir: str | Path) -> list[Path]:
    return _render_svg(pdf_path, output_dir)


def render_html(pdf_path: str | Path, output_path: str | Path, selectable_text: bool = True) -> Path:
    return _render_html(pdf_path, output_path, selectable_text)


def load_pdf_pages(pdf_path: str | Path) -> list[PageSvg]:
    return _load_pdf_pages(pdf_path)


def write_svg_pages(pages: list[PageSvg], output_dir: str | Path) -> list[Path]:
    return _write_svg_pages(pages, output_dir)


def write_html_pages(pages: list[PageSvg], output_path: str | Path, selectable_text: bool = True) -> Path:
    return _write_html_pages(pages, output_path, selectable_text)


def load_and_normalize(path: str | Path, input_format: str = "auto") -> NormalizedResume:
    data = load_resume_data(path)
    return normalize(data, input_format)


def load_resume_data(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))
