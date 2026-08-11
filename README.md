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
- `preview.html` — generated local preview
- `scripts/build-preview.mjs` — regenerates the preview

## Local preview

Open `preview.html` in a browser.


Or generate a new preview with:

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

## Custom extension: `activities`

The JSON Resume schema does not currently provide a dedicated membership/activity section with the same fields as work/education. This theme therefore supports an optional top-level `activities` array:

```json
{
  "activities": [
    {
      "organization": "University Robotics Club",
      "position": "Project Member",
      "startDate": "2024-09-01",
      "dateText": "Sep. 2024 -- Present",
      "location": { "city": "San Diego", "region": "CA" }
    },
    {
      "organization": "Hackathon Association",
      "position": "Event Volunteer",
      "startDate": "2025-02-01",
      "endDate": "2025-05-01",
      "dateText": "Feb. 2025 -- May 2025",
      "location": { "city": "Los Angeles", "region": "CA" }
    }
  ]
}
```

It also supports optional display helpers such as `dateText` and `endDateText` so wording like `(Projected) May 2029` can be reproduced exactly. Unknown/custom properties are simply ignored by other themes that do not support them.

## Attribution

Visual design adapted from the supplied LaTeX resume source credited to `jakegut/resume' and based on `sb2nov/resume`. The source states an MIT license.

## Theme API

The package is dependency-free and exports a pure `render(resume)` function. All CSS is embedded directly in the returned HTML.
