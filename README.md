# jsonresume-theme-jake-latex

A compact, ATS-friendly JSON Resume theme inspired by `Jake's Resume`'s LaTeX resume layout (itself based on the sb2nov resume template).

The theme recreates the main visual traits of the supplied LaTeX source:

- centered small-caps name and compact contact line
- letter-size print layout
- small-caps section headings with horizontal rules
- bold left / right-aligned date rows
- italic organization/location metadata rows
- dense bullet spacing
- serif typography similar to default LaTeX Computer Modern
- black-and-white, print-friendly output

## Files

- `index.js` — JSON Resume theme; exports `render(resume)`
- `resume.json` — sample data converted from the supplied LaTeX resume
- `preview.html` — generated local preview (uncensored)
- `preview-censored.html` — generated local preview with `meta.censorship` applied
- `scripts/build-preview.mjs` — regenerates both previews

## Local preview

Open `preview.html` in a browser, or `preview-censored.html` to see the same resume with `meta.censorship` applied.


Or generate new previews with:

```bash
npm run preview
```

## Use with resume-cli

Install the official CLI if needed:

```bash
npm install -g resume-cli
```

From a directory containing your `resume.json`, install this theme locally or publish it to npm, then export:

```bash
resume export resume.html --theme ./path/to/jsonresume-theme-jake-resume
```

Depending on the installed `resume-cli` version, local theme resolution can vary. A reliable development option is to install the theme package into the resume project first:

```bash
npm install ./path/to/jsonresume-theme-jake-resume
resume export resume.html --theme jsonresume-theme-jake-resume
```

For PDF output:

```bash
resume export resume.pdf --theme jsonresume-theme-jake-resume
```

## Section order: `meta.order`

Section rendering order is controlled by an optional `meta.order` array of top-level resume keys:

```json
{
  "meta": {
    "order": ["education", "work", "projects", "skills", "certificates"]
  }
}
```

Sections listed in `meta.order` render first, in the order given. Any supported section left out is appended afterwards in the theme's default order, so a partial list promotes sections rather than hiding them. Unrecognized keys and duplicates are ignored, and empty sections are omitted as usual. Without `meta.order`, the default order is:

`education`, `work`, `volunteer`, `projects`, `awards`, `certificates`, `publications`, `skills`, `languages`, `interests`, `references`

The header (`basics`) is not part of the ordering and always renders first.

## Section titles: `meta.aliases`

Section headings default to the theme's own wording (`Work`, `Volunteer`, `Certifications`, ...). An optional `meta.aliases` map overrides any of them, keyed by the same top-level resume keys used in `meta.order`:

```json
{
  "meta": {
    "aliases": {
      "work": "Experience",
      "volunteer": "Activities"
    }
  }
}
```

This renames only the heading — the section's data still comes from its standard key, and the layout of its entries is unchanged. Aliases for unrecognized keys, and values that are not a non-empty string, fall back to the default title.

## Hiding contact details: `meta.censorship`

Contact details can be withheld from the rendered header — useful for a copy posted publicly:

```json
{
  "meta": {
    "censorship": {
      "toggle": true,
      "content": ["phone", "email", "Kaggle", "LinkedIn"]
    }
  }
}
```

Censorship is opt-in: a resume without `meta.censorship`, or with `toggle` set to anything other than `true`, renders in full.

Each entry in `content` names either a `basics` field —

`name`, `label`, `email`, `phone`, `url`, `summary`, `location`

— or a single profile, matched against its `network`, `username`, or `url`. The literal key `profiles` removes every profile at once. Matching is case-insensitive, and unrecognized entries are ignored. Hiding `url` also drops its `urlLabel`, since that is only ever the link's display text.

Only the header is affected; section entries are unchanged.

`render()` takes an optional second argument that overrides the toggle, which is how one `resume.json` produces both previews:

```js
render(resume);                   // follows meta.censorship.toggle
render(resume, { censor: true }); // always applies meta.censorship.content
render(resume, { censor: false }); // always renders in full
```

It also supports optional display helpers such as `dateText` and `endDateText` so wording like `(Projected) May 2029` can be reproduced exactly. Unknown/custom properties are simply ignored by other themes that do not support them.

## Attribution

Visual design adapted from the supplied LaTeX resume source credited to `jakegut/resume` and based on `sb2nov/resume`. The source states an MIT license.

## Theme API

The package is dependency-free and exports a pure `render(resume, options?)` function. All CSS is embedded directly in the returned HTML.
