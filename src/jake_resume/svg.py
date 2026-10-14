from __future__ import annotations

from dataclasses import dataclass
from html import escape
from math import atan2, degrees, isfinite
from pathlib import Path
from urllib.parse import urlparse


class SvgRenderingError(RuntimeError):
    """Raised when a PDF cannot be converted to SVG or HTML."""


try:
    import pymupdf
except ImportError:  # pragma: no cover - exercised by installation failures
    pymupdf = None  # type: ignore[assignment]


@dataclass(frozen=True)
class _PageLink:
    href: str
    left: float
    top: float
    width: float
    height: float


@dataclass(frozen=True)
class _TextSpan:
    text: str
    x: float
    baseline: float
    width: float
    font_size: float
    rotation: float


@dataclass(frozen=True)
class PageSvg:
    number: int
    svg: str
    width: float
    height: float
    links: tuple[_PageLink, ...]
    text_spans: tuple[_TextSpan, ...] = ()


def _require_pymupdf():
    if pymupdf is None:
        raise SvgRenderingError("PyMuPDF is required for SVG and HTML output. Install the project dependencies first.")
    return pymupdf


def _safe_uri(value: object) -> str:
    uri = str(value or "").strip()
    if not uri:
        return ""
    scheme = urlparse(uri).scheme.lower()
    if scheme not in {"http", "https", "ftp", "mailto", "tel"}:
        return ""
    return uri


def _page_links(page, width: float, height: float) -> tuple[_PageLink, ...]:
    links: list[_PageLink] = []
    for link in page.get_links():
        if link.get("kind") != pymupdf.LINK_URI:
            continue
        href = _safe_uri(link.get("uri"))
        rectangle = link.get("from")
        if not href or rectangle is None or not width or not height:
            continue
        left = max(0.0, min(100.0, float(rectangle.x0) / width * 100))
        top = max(0.0, min(100.0, float(rectangle.y0) / height * 100))
        right = max(left, min(100.0, float(rectangle.x1) / width * 100))
        bottom = max(top, min(100.0, float(rectangle.y1) / height * 100))
        if right > left and bottom > top:
            links.append(_PageLink(href, left, top, right - left, bottom - top))
    return tuple(links)


def _text_spans(page) -> tuple[_TextSpan, ...]:
    """Read ordered PDF text spans without making text extraction required."""

    try:
        blocks = page.get_text("dict", sort=True).get("blocks", ())
    except Exception:
        return ()

    spans: list[_TextSpan] = []
    for block in blocks:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", ()):
            direction = line.get("dir", (1.0, 0.0))
            try:
                rotation = degrees(atan2(float(direction[1]), float(direction[0])))
            except (IndexError, TypeError, ValueError):
                rotation = 0.0
            if not isfinite(rotation):
                rotation = 0.0
            for span in line.get("spans", ()):
                text = str(span.get("text", ""))
                bbox = span.get("bbox")
                origin = span.get("origin")
                size = span.get("size")
                if not text or not bbox or not origin or size is None:
                    continue
                try:
                    x = float(origin[0])
                    baseline = float(origin[1])
                    width = max(0.0, float(bbox[2]) - float(bbox[0]))
                    font_size = float(size)
                except (IndexError, TypeError, ValueError):
                    continue
                if not all(isfinite(value) for value in (x, baseline, width, font_size)) or font_size <= 0:
                    continue
                spans.append(_TextSpan(text, x, baseline, width, font_size, rotation))
    return tuple(spans)


def _strip_xml_prologue(svg: str) -> str:
    value = svg.strip()
    if value.startswith("<?xml") and "?>" in value:
        value = value.split("?>", 1)[1].lstrip()
    return value


def load_pdf_pages(pdf_path: str | Path) -> list[PageSvg]:
    library = _require_pymupdf()
    source = Path(pdf_path).resolve()
    if not source.is_file():
        raise SvgRenderingError(f"PDF input not found: {source}")

    try:
        document = library.open(str(source))
    except Exception as exc:
        raise SvgRenderingError(f"Could not open PDF input {source}: {exc}") from exc

    pages: list[PageSvg] = []
    try:
        if len(document) == 0:
            raise SvgRenderingError(f"PDF contains no pages: {source}")
        for index, page in enumerate(document):
            width = float(page.rect.width)
            height = float(page.rect.height)
            pages.append(
                PageSvg(
                    number=index + 1,
                    svg=_strip_xml_prologue(page.get_svg_image()),
                    width=width,
                    height=height,
                    links=_page_links(page, width, height),
                    text_spans=_text_spans(page),
                )
            )
    except SvgRenderingError:
        raise
    except Exception as exc:
        raise SvgRenderingError(f"Could not convert PDF pages from {source}: {exc}") from exc
    finally:
        document.close()
    return pages


def render_svg(pdf_path: str | Path, output_dir: str | Path) -> list[Path]:
    """Convert every page in a PDF to a numbered SVG file."""

    return write_svg_pages(load_pdf_pages(pdf_path), output_dir)


def write_svg_pages(pages: list[PageSvg], output_dir: str | Path) -> list[Path]:
    """Write already-converted PDF pages as numbered SVG files."""

    destination = Path(output_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    output_paths: list[Path] = []
    for page in pages:
        path = destination / f"page-{page.number}.svg"
        path.write_text(page.svg, encoding="utf-8")
        output_paths.append(path)
    return output_paths


def _link_markup(page: PageSvg) -> str:
    anchors = []
    for link in page.links:
        style = (
            f"left:{link.left:.6f}%;top:{link.top:.6f}%;"
            f"width:{link.width:.6f}%;height:{link.height:.6f}%;"
        )
        anchors.append(
            f'<a class="pdf-link" href="{escape(link.href, quote=True)}" '
            f'aria-label="Open link" style="{style}"></a>'
        )
    return "".join(anchors)


def _text_layer_markup(page: PageSvg) -> str:
    if not page.text_spans:
        return ""
    text_markup = []
    for span in page.text_spans:
        attributes = (
            f'x="{span.x:.6f}" y="{span.baseline:.6f}" '
            f'font-size="{span.font_size:.6f}" '
            f'textLength="{span.width:.6f}" lengthAdjust="spacingAndGlyphs"'
        )
        if span.rotation:
            attributes += f' transform="rotate({span.rotation:.6f} {span.x:.6f} {span.baseline:.6f})"'
        text_markup.append(f"<text {attributes}>{escape(span.text)}</text>")
    return (
        f'<svg class="text-layer" aria-hidden="true" focusable="false" xml:space="preserve" '
        f'viewBox="0 0 {page.width:g} {page.height:g}" preserveAspectRatio="none">'
        + "".join(text_markup)
        + "</svg>"
    )


def _html_document(pages: list[PageSvg], selectable_text: bool = True) -> str:
    page_markup = []
    for page in pages:
        text_layer = _text_layer_markup(page) if selectable_text else ""
        page_markup.append(
            f'<section class="resume-page" aria-label="Page {page.number}">'
            f'<div class="resume-page-content">{page.svg}{text_layer}{_link_markup(page)}</div>'
            "</section>"
        )

    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Resume</title>
  <style>
    :root { color-scheme: light; }
    * { box-sizing: border-box; }
    html, body { min-height: 100%; margin: 0; }
    body {
      background: #e9e9e9;
      color: #000;
      overflow-y: auto;
      font-family: sans-serif;
    }
    .resume-pages {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1rem;
      min-height: 100vh;
      padding: 1rem;
    }
    .resume-page {
      width: min(100%, 8.5in);
      flex: 0 0 auto;
      background: #fff;
      box-shadow: 0 1px 5px rgb(0 0 0 / 18%);
    }
    .resume-page-content {
      position: relative;
      width: 100%;
      line-height: 0;
    }
    .resume-page-content > svg {
      display: block;
      width: 100%;
      height: auto;
    }
    .resume-page-content > .text-layer {
      position: absolute;
      inset: 0;
      z-index: 1;
      width: 100%;
      height: 100%;
      overflow: visible;
      user-select: text;
    }
    .text-layer text {
      fill: transparent;
      stroke: none;
      pointer-events: all;
      user-select: text;
    }
    .pdf-link {
      position: absolute;
      display: block;
      z-index: 2;
    }
    @media print {
      .resume-pages { gap: 0; padding: 0; }
      .resume-page { width: 100%; box-shadow: none; break-after: page; }
      .resume-page:last-child { break-after: auto; }
    }
  </style>
</head>
<body>
  <main class="resume-pages">
    """ + "\n    ".join(page_markup) + """
  </main>
</body>
</html>
"""


def render_html(pdf_path: str | Path, output_path: str | Path, selectable_text: bool = True) -> Path:
    """Write a self-contained, scrollable HTML wrapper for a PDF's pages."""

    return write_html_pages(load_pdf_pages(pdf_path), output_path, selectable_text)


def write_html_pages(pages: list[PageSvg], output_path: str | Path, selectable_text: bool = True) -> Path:
    """Write a self-contained HTML wrapper from converted PDF pages."""

    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_html_document(pages, selectable_text), encoding="utf-8")
    return output


__all__ = [
    "PageSvg",
    "SvgRenderingError",
    "load_pdf_pages",
    "render_html",
    "render_svg",
    "write_html_pages",
    "write_svg_pages",
]
