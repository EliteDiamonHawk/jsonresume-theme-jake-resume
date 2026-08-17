# jsonresume-theme-jake-resume-minimal

An ATS-friendly, print-ready [JSON Resume](https://jsonresume.org/) theme inspired by Jake Gutierrez's LaTeX resume layout. This is the schema-only variant: it uses standard JSON Resume fields without theme-specific ordering, alias, censorship, or display-text controls.

## Install and use

From this directory, install dependencies and build the example preview:

```sh
npm install
npm run preview
```

This writes `preview.html` from the included `resume.json`. Open it in a browser and use the print dialog to save a PDF. The generated document contains its own CSS, including letter-size page and print rules.

Use the theme programmatically by importing `render`. It returns a complete HTML document.

```js
import { readFile } from "node:fs/promises";
import { render } from "jsonresume-theme-jake-resume-minimal";

const resume = JSON.parse(await readFile("resume.json", "utf8"));
const html = render(resume);
```

## Supported resume content

The renderer accepts a JSON Resume object and displays `basics` plus these top-level arrays when they contain items:

`education`, `work`, `volunteer`, `projects`, `awards`, `certificates`, `publications`, `skills`, `languages`, `interests`, and `references`.

The section order is fixed: education, work, volunteer, projects, awards, certificates, publications, skills, languages, interests, then references. Empty sections are omitted.

For familiar JSON Resume fields, the theme formats dates as month/year where available, combines location-object components into a readable string, and renders URLs as links. `basics.profiles` use the profile network as their link label. The included [resume.json](resume.json) is a complete working example.

The `meta.canonical`, `meta.lastModified`, and `meta.version` fields are included in the output document metadata when supplied.

## Choosing a variant

Use this minimal package when your resume must remain within the standard JSON Resume schema. Use the sibling `jsonresume-theme-jake-resume-extra` package when you need custom section headings or ordering, display-date text, custom URL labels, string locations, or contact-detail censorship.

## Development

```sh
npm test
npm run preview
```

`npm test` checks representative standard-schema rendering, including certificate links and object locations. The package is self-contained; edit `index.js` to change presentation and `resume.json` to update the sample.

## License

[MIT](LICENSE)
