# jsonresume-theme-jake-resume-extra

An ATS-friendly, print-ready [JSON Resume](https://jsonresume.org/) theme inspired by Jake Gutierrez's LaTeX resume layout. This is the extended variant: it supports the standard resume fields as well as optional display controls for tailoring the rendered document.

## Install and use

From this directory, install the package dependencies and create a local preview:

```sh
npm install
npm run preview
```

The preview command renders `resume.json` twice:

- `preview.html` contains the full resume.
- `preview-censored.html` applies the configured contact-detail censorship.

Open either file in a browser and use the browser's print dialog to save a PDF. The theme includes letter-size page rules and print styles.

To render a resume in an application, import `render`. It returns a complete HTML document with its CSS embedded.

```js
import { readFile } from "node:fs/promises";
import { render } from "jsonresume-theme-jake-resume-extra";

const resume = JSON.parse(await readFile("resume.json", "utf8"));
const html = render(resume);
```

Pass `{ censor: false }` to force the full version or `{ censor: true }` to force the censored version, regardless of the setting in the resume file.

```js
const fullHtml = render(resume, { censor: false });
const shareableHtml = render(resume, { censor: true });
```

## Supported resume content

The theme renders `basics` plus these top-level JSON Resume arrays when they contain items: `education`, `work`, `volunteer`, `projects`, `awards`, `certificates`, `publications`, `skills`, `languages`, `interests`, and `references`.

The extensions below are optional. A normal JSON Resume renders without them. See the included [resume.json](resume.json) for a complete example.

## Header image

Set the standard `basics.image` field to an absolute `http://` or `https://` image URL. PNG, JPEG, SVG, and other browser-supported image formats work without conversion; local paths and data URIs are ignored. The image sits to the right of the header, is square, and is centered and cropped with `object-fit: cover` to match the header height.

```json
{
  "basics": {
    "image": "https://example.com/images/profile.png"
  }
}
```

## Section ordering

Use `meta.order` to move known sections to the front in a custom order. Sections omitted from the list still render afterward in the theme's normal order; unknown and duplicate keys are ignored.

```json
{
  "meta": {
    "order": ["education", "work", "projects", "skills"]
  }
}
```

## Section aliases

Use `meta.aliases` to replace a section heading. Keys must be supported top-level section names and values must be non-empty strings.

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

## Contact-detail censorship

Censorship is off by default. Add `meta.censorship` with `toggle: true` to make `render(resume)` hide the specified details. The included sample keeps `toggle` set to `false`; `npm run preview` explicitly produces both a full and a censored preview.

```json
{
  "meta": {
    "censorship": {
      "toggle": true,
      "content": ["email", "phone", "LinkedIn"]
    }
  }
}
```

`content` can name basic fields (`name`, `label`, `email`, `phone`, `url`, `summary`, or `location`), `profiles` to remove every profile, or a profile's network, username, or URL. Matching is case-insensitive. The `render(resume, { censor: true })` and `render(resume, { censor: false })` options override `toggle` for a single render.

## Display-date text

Standard dates in `YYYY-MM` or `YYYY-MM-DD` form display as abbreviated month and year. Supply a display-text field when the exact wording matters: `dateText` for dated entries, `startDateText` or `endDateText` for ranges, and `releaseDateText` for publications.

```json
{
  "projects": [
    {
      "name": "Ferry Schedule Scraper",
      "dateText": "Summer 2024"
    }
  ]
}
```

## Custom URL labels

Set `basics.urlLabel` to replace the default `Website` label in the header. Set `urlLabel` on projects, certificates, or publications to replace their default link label.

```json
{
  "certificates": [
    {
      "name": "Example Credential",
      "url": "https://example.com/verify",
      "urlLabel": "Verify"
    }
  ]
}
```

## String locations

Alongside JSON Resume location objects, this variant accepts a ready-to-display string for `basics.location` and entry locations. Use it when you need exact punctuation or a compact location format.

```json
{
  "basics": {
    "location": "Oakland, CA, US"
  }
}
```

## Document metadata

`meta.language`, `meta.canonical`, `meta.lastModified`, and `meta.version` are emitted as document metadata when present.

## Development

```sh
npm test
npm run preview
```

`npm test` exercises the renderer, including aliases, censorship, and both object and string locations. The package is self-contained; edit `index.js` to change rendering and `resume.json` to update the sample.

## License

[MIT](LICENSE)
