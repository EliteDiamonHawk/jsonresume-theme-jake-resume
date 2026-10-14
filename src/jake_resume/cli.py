from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

from .adapters import InputError, normalize
from .censorship import CensorshipError, apply_censorship, load_censorship_file
from .render import (
    CompilationError,
    compile_pdf,
    load_and_normalize,
    load_pdf_pages,
    load_resume_data,
    render_latex,
    write_html_pages,
    write_svg_pages,
)


FORMAT_ORDER = ("latex", "pdf", "svg", "html")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jake-resume", description="Convert JSON Resume or RxResume data through Jake-style LaTeX to PDF, SVG, or HTML.")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="validate and normalize a JSON resume document")
    validate.add_argument("input", type=Path)
    validate.add_argument("--input-format", choices=["auto", "jsonresume", "rxresume-v5"], default="auto")

    render = sub.add_parser("render", help="render a resume as LaTeX, PDF, SVG, or HTML")
    render.add_argument("input", type=Path)
    render.add_argument(
        "--format",
        "-f",
        action="append",
        required=True,
        metavar="FORMAT[,FORMAT...]",
        help="one or more formats: latex, tex, pdf, svg, html, or all; repeat the flag or separate values with commas",
    )
    outputs = render.add_mutually_exclusive_group(required=True)
    outputs.add_argument("--output", "-o", type=Path)
    outputs.add_argument("--output-dir", "-d", type=Path)
    render.add_argument("--input-format", choices=["auto", "jsonresume", "rxresume-v5"], default="auto")
    render.add_argument("--engine", "-e", choices=["pdflatex", "xelatex", "lualatex"], default="pdflatex")
    render.add_argument("--latex-output", "-l", dest="latex_output", type=Path, help="retain the intermediate LaTeX source")
    render.add_argument("--tex-output", dest="latex_output", type=Path, help=argparse.SUPPRESS)
    render.add_argument("--warnings", "-w", choices=["show", "error"], default="show")
    render.add_argument("--censorship-file", "-c", type=Path)
    render.add_argument("--no-text-selection", action="store_true", help="omit the selectable text layer from HTML output")
    return parser


def _print_diagnostics(resume, warnings_mode: str = "show") -> int:
    for diagnostic in resume.diagnostics:
        print(diagnostic, file=sys.stderr)
    if warnings_mode == "error" and resume.warnings:
        return 2
    return 0


def _prepare_resume(data, input_format: str, censorship_paths: list[str] | None = None):
    if censorship_paths is None:
        return normalize(data, input_format)
    censored, diagnostics = apply_censorship(data, censorship_paths)
    resume = normalize(censored, input_format)
    resume.diagnostics.extend(diagnostics)
    return resume


def _normalize_formats(raw_formats: list[str]) -> list[str]:
    tokens: list[str] = []
    for raw_format in raw_formats:
        parts = [part.strip().lower() for part in raw_format.split(",")]
        if any(not part for part in parts):
            raise InputError("--format contains an empty format name.")
        tokens.extend(parts)

    unique_tokens = list(dict.fromkeys(tokens))
    if "all" in unique_tokens:
        if len(unique_tokens) != 1:
            raise InputError("--format all cannot be combined with other formats.")
        return list(FORMAT_ORDER)

    aliases = {"tex": "latex"}
    canonical: set[str] = set()
    for token in unique_tokens:
        value = aliases.get(token, token)
        if value not in FORMAT_ORDER:
            choices = ", ".join((*FORMAT_ORDER, "all"))
            raise InputError(f"Unsupported output format '{token}'. Choose from {choices}.")
        canonical.add(value)
    return [format_name for format_name in FORMAT_ORDER if format_name in canonical]


def _base_path(path: Path) -> Path:
    if path.suffix.lower() in {".tex", ".pdf", ".svg", ".html"}:
        return path.with_suffix("")
    return path


def _output_paths(output: Path, formats: list[str], expand: bool) -> dict[str, Path]:
    if not expand:
        return {formats[0]: output.resolve()}

    base = _base_path(output.resolve())
    return {
        "latex": base.with_suffix(".tex"),
        "pdf": base.with_suffix(".pdf"),
        "svg": base.parent / f"{base.name}-svg",
        "html": base.with_suffix(".html"),
    }


def _write_formats(
    resume,
    output: Path,
    formats: list[str],
    engine: str,
    latex_output: Path | None,
    expand: bool,
    selectable_text: bool = True,
) -> list[Path]:
    latex = render_latex(resume)
    if len(formats) > 1 and latex_output is not None:
        raise InputError("--latex-output cannot be used with multiple formats; the shared .tex output is automatic.")
    if formats == ["latex"] and latex_output is not None:
        raise InputError("--latex-output is only used with PDF, SVG, or HTML output.")

    paths = _output_paths(output, formats, expand)
    if "latex" in formats:
        tex_path = paths["latex"]
        tex_path.parent.mkdir(parents=True, exist_ok=True)
        tex_path.write_text(latex, encoding="utf-8")
    elif latex_output is not None:
        tex_path = latex_output.resolve()
        tex_path.parent.mkdir(parents=True, exist_ok=True)
        tex_path.write_text(latex, encoding="utf-8")

    needs_pdf = any(format_name in formats for format_name in ("pdf", "svg", "html"))
    compiled_pdf: Path | None = None
    temporary_pdf: Path | None = None
    if needs_pdf:
        if "pdf" in formats:
            compiled_pdf = paths["pdf"]
        else:
            output_parent = output.resolve().parent
            output_parent.mkdir(parents=True, exist_ok=True)
            temporary_pdf = output_parent / f".{_base_path(output).name}-{uuid.uuid4().hex}.pdf"
            compiled_pdf = temporary_pdf
    try:
        if compiled_pdf is not None:
            compile_pdf(latex, compiled_pdf, engine)
        if "svg" in formats or "html" in formats:
            pages = load_pdf_pages(compiled_pdf)
            if "svg" in formats:
                write_svg_pages(pages, paths["svg"])
            if "html" in formats:
                write_html_pages(pages, paths["html"], selectable_text)
    finally:
        if temporary_pdf is not None:
            temporary_pdf.unlink(missing_ok=True)
    return [paths[format_name] for format_name in formats]


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate":
            resume = load_and_normalize(args.input, args.input_format)
            print(json.dumps({"format": resume.format, "sections": [section.title for section in resume.sections], "warnings": len(resume.warnings)}, indent=2))
            return _print_diagnostics(resume)

        formats = _normalize_formats(args.format) if args.command == "render" else None
        if args.no_text_selection and "html" not in formats:
            raise InputError("--no-text-selection requires HTML output.")

        if args.output_dir is not None:
            if args.censorship_file is None:
                raise InputError("--output-dir requires --censorship-file.")
            if args.latex_output is not None:
                raise InputError("--latex-output cannot be used with --output-dir.")

        data = load_resume_data(args.input)
        censorship_paths = load_censorship_file(args.censorship_file) if args.censorship_file else None
        if args.output_dir is not None:
            normal = _prepare_resume(data, args.input_format)
            censored = _prepare_resume(data, args.input_format, censorship_paths)
            if args.warnings == "error" and (normal.warnings or censored.warnings):
                _print_diagnostics(normal, args.warnings)
                _print_diagnostics(censored, args.warnings)
                return 2
            args.output_dir.mkdir(parents=True, exist_ok=True)
            normal_output = args.output_dir / args.input.stem / args.input.stem
            censored_output = args.output_dir / f"{args.input.stem}-censored" / f"{args.input.stem}-censored"
            normal_paths = _write_formats(normal, normal_output, formats, args.engine, None, True, not args.no_text_selection)
            censored_paths = _write_formats(censored, censored_output, formats, args.engine, None, True, not args.no_text_selection)
            _print_diagnostics(normal, args.warnings)
            _print_diagnostics(censored, args.warnings)
            for path in (*normal_paths, *censored_paths):
                print(f"Wrote {path.resolve()}")
            return 0

        resume = _prepare_resume(data, args.input_format, censorship_paths)
        if args.warnings == "error" and resume.warnings:
            _print_diagnostics(resume, args.warnings)
            return 2
        paths = _write_formats(
            resume,
            args.output,
            formats,
            args.engine,
            args.latex_output,
            len(formats) > 1,
            not args.no_text_selection,
        )
        _print_diagnostics(resume, args.warnings)
        for path in paths:
            print(f"Wrote {path.resolve()}")
        return 0
    except (CensorshipError, InputError, json.JSONDecodeError, OSError, CompilationError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
