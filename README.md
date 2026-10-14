# jake-resume

`jake-resume` converts JSON Resume and RxResume documents into Jake-style LaTeX, PDF, SVG, and HTML.

The renderer uses one visual source:

```text
JSON Resume or RxResume -> LaTeX -> PDF -> SVG pages -> HTML wrapper
```

The LaTeX layout uses a compact, one-column Letter page with a centered serif header, underlined links, ruled section headings, right-aligned dates, and compact entries.

## Credits
This repo is based on Jake Gutierrez's `Jake's Resume` found at [overleaf.com/latex/templates/jakes-resume](https://www.overleaf.com/latex/templates/jakes-resume)

## Install

Install the Python package with [uv](https://docs.astral.sh/uv/):

```powershell
uv sync
```

PDF, SVG, and HTML output require a LaTeX compiler. The CLI supports `pdflatex`, `xelatex`, and `lualatex`. Install MiKTeX or TeX Live and make the compiler available on `PATH`.

The generated source is engine-aware. `pdflatex` uses its built-in glyph-to-Unicode mapping, while `xelatex` and `lualatex` use Unicode fonts. To render Japanese, Chinese, or Korean text with the Unicode engines, install the `fontspec`, `xeCJK`, and `luatexja-fontspec` packages and the `Noto Serif CJK JP` font. MiKTeX may offer to install the packages automatically; the font must be available to the TeX engine.

For example, render PDF and HTML with LuaLaTeX:

```powershell
uv run jake-resume render fixtures\01-minimal-native.json `
  --format pdf,html `
  --engine lualatex `
  --output build\01-minimal-native
```

## Use

Validate an input file:

```powershell
uv run jake-resume validate resume.json
uv run jake-resume validate resume.json --input-format rxresume-v5
```

Write LaTeX:

```powershell
uv run jake-resume render resume.json `
  --format latex `
  --output build\resume.tex
```

`--format tex` remains an alias for `latex`.

Request several formats with commas or repeated flags:

```powershell
uv run jake-resume render resume.json `
  --format pdf,svg `
  --output build\resume

uv run jake-resume render resume.json `
  --format pdf `
  --format svg `
  --output build\resume
```

Use `--format all` for LaTeX, PDF, SVG, and HTML:

```powershell
uv run jake-resume render resume.json `
  --format all `
  --output build\resume
```

Multi-format output uses the base path to create `resume.tex`, `resume.pdf`, `resume-svg\page-1.svg`, and `resume.html`. The command renders LaTeX once, compiles one PDF, and shares one PDF-to-SVG conversion across SVG and HTML output.

Compile a PDF:

```powershell
uv run jake-resume render resume.json `
  --format pdf `
  --output build\resume.pdf
```

Convert the PDF pages to SVG:

```powershell
uv run jake-resume render resume.json `
  --format svg `
  --output build\resume-svg
```

The CLI writes one file per PDF page: `page-1.svg`, `page-2.svg`, and so on.

Write a self-contained HTML page:

```powershell
uv run jake-resume render resume.json `
  --format html `
  --output build\resume.html
```

The HTML file embeds every SVG page. The browser stacks the pages vertically and lets you scroll through the document. PDF web, email, telephone, and FTP links remain clickable in the HTML wrapper.

HTML output includes a selectable text layer by default, while preserving the SVG visual rendering. Pass `--no-text-selection` to omit that layer when a purely visual HTML output is preferred.

Keep the intermediate LaTeX source when compiling another format:

```powershell
uv run jake-resume render resume.json `
  --format html `
  --output build\resume.html `
  --latex-output build\resume.tex
```

## Input behavior

The renderer keeps every non-empty input section and custom RxResume section. It does not force arbitrary data into fixed Education, Experience, or Skills sections.

RxResume layout metadata controls section order and hidden state. Jake's layout controls page size, typography, colors, sidebars, icons, and picture styling.

The renderer recognizes common title, organization, subtitle, location, and date fields. It supports `period`, `dates`, `dateRange`, `date`, start and end values, and `present`. Other user-facing fields remain visible as compact text or bullets.

Profiles appear as header links. Email, phone, websites, profile links, and certificate links become clickable links in the PDF and HTML output. RxResume implementation fields such as `id`, `icon`, `iconColor`, and `inlineLink` stay out of the rendered document.

## Censorship

Use a JSON censorship file to remove exact dotted paths from an in-memory copy before rendering:

```json
{
  "remove": [
    "basics.email",
    "basics.phone"
  ]
}
```

```powershell
uv run jake-resume render resume.json `
  --format pdf `
  --output build\resume-censored.pdf `
  --censorship-file examples\censorship.json
```

Use `--warnings error` to fail when a censorship path or another diagnostic reports a warning.

Pass `--output-dir` with a censorship file to create normal and censored output directories. Each directory contains the requested formats. SVG renders use a page directory inside the matching variant directory.

## Development

Run the Python test suite:

```powershell
uv run python -m unittest discover -s tests -v
```

The Python package owns normalization, LaTeX generation, PDF compilation, PDF-to-SVG conversion, and HTML wrapping. The generated LaTeX stays temporary unless you pass `--latex-output`.
