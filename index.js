const css = String.raw`
@page {
  size: letter;
  margin: 0.48in 0.55in 0.48in;
}

* { box-sizing: border-box; }

html, body {
  margin: 0;
  padding: 0;
  background: #fff;
  color: #000;
}

body {
  font-family: "Latin Modern Roman", "CMU Serif", "Computer Modern", "Times New Roman", Times, serif;
  font-size: 11pt;
  line-height: 1.16;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

.resume {
  width: 100%;
  max-width: 8.5in;
  margin: 0 auto;
}

.header {
  text-align: center;
  margin: 0 0 10px;
}

.name {
  margin: 0 0 4px;
  font-size: 25pt;
  line-height: 1;
  font-weight: 700;
  font-variant: small-caps;
  letter-spacing: 0.2px;
}

.label {
  margin: 0 0 3px;
  font-size: 10pt;
  font-style: italic;
}

.contact {
  font-size: 9.4pt;
  line-height: 1.25;
}

.contact a,
.inline-link {
  color: inherit;
  text-decoration: underline;
  text-underline-offset: 1px;
}

.sep {
  padding: 0 4px;
}

.summary {
  margin: 5px 0 0;
  font-size: 9.7pt;
  text-align: left;
}

.section {
  margin: 7px 0 0;
  break-inside: auto;
}

.section-title {
  margin: 0 0 5px;
  padding: 0 0 2px;
  border-bottom: 0.8px solid #000;
  font-size: 12pt;
  line-height: 1.05;
  font-weight: 400;
  font-variant: small-caps;
  letter-spacing: 0.35px;
}

.entries {
  margin: 0;
  padding: 0 0 0 0.15in;
  list-style: none;
}

.entry {
  margin: 0 0 6px;
  break-inside: avoid;
}

.entry:last-child {
  margin-bottom: 0;
}

.row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  column-gap: 16px;
  align-items: baseline;
}

.primary {
  font-weight: 700;
  min-width: 0;
}

.secondary,
.meta-left,
.meta-right {
  font-style: italic;
  font-size: 9.7pt;
}

.right {
  text-align: right;
  white-space: nowrap;
}

.meta-row {
  margin-top: 1px;
}

.project-title {
  min-width: 0;
  font-size: 9.7pt;
}

.project-title strong {
  font-weight: 700;
}

.project-tech {
  font-style: italic;
}

.bullets {
  margin: 3px 0 0 0.21in;
  padding: 0 0 0 0.16in;
}

.bullets li {
  margin: 0 0 2px;
  padding-left: 1px;
  font-size: 9.7pt;
}

.bullets li:last-child {
  margin-bottom: 0;
}

.compact-lines {
  margin: 1px 0 0;
  padding: 0 0 0 0.15in;
  list-style: none;
  font-size: 9.7pt;
}

.compact-line {
  margin: 0 0 3px;
}

.compact-line:last-child {
  margin-bottom: 0;
}

.compact-label {
  font-weight: 700;
}

.plain-note {
  margin: 3px 0 0;
  font-size: 9.7pt;
}

@media screen {
  body {
    background: #ececec;
    padding: 24px 0;
  }

  .resume {
    width: 8.5in;
    min-height: 11in;
    padding: 0.48in 0.55in;
    background: #fff;
    box-shadow: 0 2px 12px rgba(0,0,0,.15);
  }
}

@media print {
  .resume {
    max-width: none;
  }

  a {
    color: #000;
  }
}
`;

function esc(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function normalizeUrl(value = "") {
  if (!value) return "";

  if (/^(https?:|mailto:|tel:)/i.test(value)) {
    return value;
  }

  return `https://${value}`;
}

function link(url, label, className = "inline-link") {
  if (!url || !label) {
    return esc(label || "");
  }

  return `<a class="${esc(className)}" href="${esc(
    normalizeUrl(url)
  )}">${esc(label)}</a>`;
}

function monthYear(value) {
  if (!value) {
    return "";
  }

  const match = String(value).match(/^(\d{4})-(\d{2})/);

  if (!match) {
    return String(value);
  }

  const year = Number(match[1]);
  const month = Number(match[2]);

  if (month < 1 || month > 12) {
    return String(value);
  }

  const names = [
    "Jan.",
    "Feb.",
    "Mar.",
    "Apr.",
    "May",
    "Jun.",
    "Jul.",
    "Aug.",
    "Sep.",
    "Oct.",
    "Nov.",
    "Dec."
  ];

  return `${names[month - 1]} ${year}`;
}

function singleDate(item = {}, field = "date") {
  const textField = `${field}Text`;

  return item[textField] || monthYear(item[field]);
}

function dateRange(item = {}) {
  if (item.dateText) {
    return item.dateText;
  }

  const start =
    item.startDateText ||
    monthYear(item.startDate);

  let end =
    item.endDateText ||
    monthYear(item.endDate);

  if (!end && start) {
    end = "Present";
  }

  return [start, end]
    .filter(Boolean)
    .join(" -- ");
}

function locationText(location = {}) {
  if (!location) {
    return "";
  }

  if (typeof location === "string") {
    return location;
  }

  return [
    location.city,
    location.region,
    location.countryCode
  ]
    .filter(Boolean)
    .join(", ");
}

function arrayOrEmpty(value) {
  return Array.isArray(value)
    ? value
    : [];
}

function bullets(items = []) {
  const clean = arrayOrEmpty(items)
    .filter(Boolean);

  if (!clean.length) {
    return "";
  }

  return `
    <ul class="bullets">
      ${clean
        .map(
          item => `<li>${esc(item)}</li>`
        )
        .join("")}
    </ul>
  `;
}

function entry({
  title = "",
  titleHtml = "",
  rightTop = "",
  subtitle = "",
  subtitleHtml = "",
  rightBottom = "",
  highlights = [],
  note = ""
}) {
  const renderedTitle =
    titleHtml ||
    esc(title);

  const renderedSubtitle =
    subtitleHtml ||
    esc(subtitle);

  return `
    <li class="entry">

      <div class="row">
        <div class="primary">
          ${renderedTitle}
        </div>

        <div class="right">
          ${esc(rightTop)}
        </div>
      </div>

      ${
        subtitle ||
        subtitleHtml ||
        rightBottom
          ? `
            <div class="row meta-row">

              <div class="meta-left">
                ${renderedSubtitle}
              </div>

              <div class="meta-right right">
                ${esc(rightBottom)}
              </div>

            </div>
          `
          : ""
      }

      ${
        note
          ? `<div class="plain-note">${esc(note)}</div>`
          : ""
      }

      ${bullets(highlights)}

    </li>
  `;
}

function section(title, body) {
  if (!body) {
    return "";
  }

  return `
    <section class="section">

      <h2 class="section-title">
        ${esc(title)}
      </h2>

      ${body}

    </section>
  `;
}

/*
|--------------------------------------------------------------------------
| SECTION FORMATS
|--------------------------------------------------------------------------
|
| Every visible section (everything except the header and meta) is built
| from one of the formats below. A section renderer only maps JSON Resume
| fields onto a format; it never emits markup of its own.
|
| A. roleEntry     -- what / when over where
| B. studyEntry    -- mirror of A: where / what over when
| C. creditEntry   -- one title, one date, one linked source line
| D. projectEntry  -- bold name | tech list, date right
| E. labelLine     -- "Label: a; b; c" one-liner
|
| Formats A-D are laid out by entry(); E is a compact list item.
|
|--------------------------------------------------------------------------
*/

/*
 * Joins optional meta fragments with the
 * pipe separator used across the theme:
 *
 * Issuer | Credential
 */
function joinMeta(parts) {
  return arrayOrEmpty(parts)
    .filter(Boolean)
    .join(" | ");
}

/*
 * JSON Resume carries a prose field
 * (summary / description) alongside
 * highlights.
 *
 * It is rendered as the first bullet.
 */
function withLeadingHighlight(text, highlights) {
  const list = arrayOrEmpty(highlights)
    .filter(Boolean);

  if (text && !list.includes(text)) {
    list.unshift(text);
  }

  return list;
}

/*
 * Renders the source line shared by
 * formats C and D:
 *
 * Publisher | Publication Link
 */
function sourceHtml({
  detail = "",
  url = "",
  urlLabel = ""
}) {
  return joinMeta([
    detail
      ? esc(detail)
      : "",

    url
      ? link(url, urlLabel)
      : ""
  ]);
}

/*
| FORMAT A
|
| Position                        Dates
| Organization                    Location
*/
function roleEntry({
  role = "",
  organization = "",
  date = "",
  location = "",
  summary = "",
  highlights = []
}) {
  return entry({
    title: role,
    rightTop: date,
    subtitle: organization,
    rightBottom: location,
    highlights: withLeadingHighlight(
      summary,
      highlights
    )
  });
}

/*
| FORMAT B
|
| Institution                     Location
| Degree in Area                  Dates
*/
function studyEntry({
  institution = "",
  location = "",
  study = "",
  date = "",
  highlights = []
}) {
  return entry({
    title: institution,
    rightTop: location,
    subtitle: study,
    rightBottom: date,
    highlights
  });
}

/*
| FORMAT C
|
| Name                            Date
| Source | Link
*/
function creditEntry({
  name = "",
  date = "",
  detail = "",
  url = "",
  urlLabel = "",
  highlights = [],
  note = ""
}) {
  return entry({
    title: name,
    rightTop: date,
    subtitleHtml: sourceHtml({
      detail,
      url,
      urlLabel
    }),
    highlights,
    note
  });
}

/*
| FORMAT D
|
| Name | Tech, Tech, Tech         Dates
| Role: ... | Project Link
*/
function projectEntry({
  name = "",
  keywords = [],
  date = "",
  detail = "",
  url = "",
  urlLabel = "",
  summary = "",
  highlights = []
}) {
  const techText = arrayOrEmpty(keywords)
    .filter(Boolean)
    .join(", ");

  const titleHtml = `
    <div class="project-title">

      <strong>
        ${esc(name)}
      </strong>

      ${
        techText
          ? `
            <span>|</span>
            <span class="project-tech">
              ${esc(techText)}
            </span>
          `
          : ""
      }

    </div>
  `;

  return entry({
    titleHtml,
    rightTop: date,
    subtitleHtml: sourceHtml({
      detail,
      url,
      urlLabel
    }),
    highlights: withLeadingHighlight(
      summary,
      highlights
    )
  });
}

/*
| FORMAT E
|
| Label: value; value; value
*/
function labelLine(label, parts = []) {
  const detail = arrayOrEmpty(parts)
    .filter(Boolean)
    .join("; ");

  return `
    <li class="compact-line">

      <span class="compact-label">
        ${esc(label)}
      </span>

      ${
        detail
          ? `: ${esc(detail)}`
          : ""
      }

    </li>
  `;
}

/*
 * Section wrappers: guard against empty
 * data, map each item through a format,
 * and wrap the result in the matching list.
 */
function entrySection(title, items, format) {
  const list = arrayOrEmpty(items);

  if (!list.length) {
    return "";
  }

  return section(
    title,
    `<ul class="entries">${list
      .map(format)
      .join("")}</ul>`
  );
}

function labelSection(title, items, format) {
  const list = arrayOrEmpty(items);

  if (!list.length) {
    return "";
  }

  return section(
    title,
    `<ul class="compact-lines">${list
      .map(format)
      .join("")}</ul>`
  );
}

/*
|--------------------------------------------------------------------------
| BASICS / HEADER
|--------------------------------------------------------------------------
*/

function renderHeader(basics = {}) {
  const location =
    locationText(basics.location);

  const contacts = [];

  if (location) {
    contacts.push(
      esc(location)
    );
  }

  if (basics.phone) {
    contacts.push(
      `<a href="${esc(
        `tel:${basics.phone}`
      )}">${esc(basics.phone)}</a>`
    );
  }

  if (basics.email) {
    contacts.push(
      `<a href="${esc(
        `mailto:${basics.email}`
      )}">${esc(basics.email)}</a>`
    );
  }

  /*
   * Profiles display the network name instead
   * of the raw URL.
   *
   * Example:
   *
   * LinkedIn | GitHub | Portfolio
   *
   * The links remain clickable.
   */
  for (const profile of basics.profiles || []) {
    const label =
      profile.network ||
      profile.username ||
      profile.url;

    const href =
      profile.url;

    if (label && href) {
      contacts.push(
        `<a href="${esc(
          normalizeUrl(href)
        )}">${esc(label)}</a>`
      );
    }
  }

  /*
   * basics.url is displayed as "Website"
   * unless urlLabel is provided.
   */
  if (basics.url) {
    const websiteLabel =
      basics.urlLabel ||
      "Website";

    contacts.push(
      `<a href="${esc(
        normalizeUrl(basics.url)
      )}">${esc(websiteLabel)}</a>`
    );
  }

  return `
    <header class="header">

      <h1 class="name">
        ${esc(basics.name || "")}
      </h1>

      ${
        basics.label
          ? `
            <div class="label">
              ${esc(basics.label)}
            </div>
          `
          : ""
      }

      <div class="contact">
        ${contacts.join(
          '<span class="sep">|</span>'
        )}
      </div>

      ${
        basics.summary
          ? `
            <div class="summary">
              ${esc(basics.summary)}
            </div>
          `
          : ""
      }

    </header>
  `;
}

/*
|--------------------------------------------------------------------------
| EDUCATION
|--------------------------------------------------------------------------
*/

function renderEducation(items = [], title = "Education") {
  return entrySection(title, items, item => {
    const notes = [];

    if (
      Array.isArray(item.courses) &&
      item.courses.length
    ) {
      notes.push(
        `Relevant Coursework: ${item.courses.join(", ")}`
      );
    }

    if (item.score) {
      notes.push(
        `GPA: ${item.score}`
      );
    }

    notes.push(
      ...arrayOrEmpty(item.highlights)
    );

    return studyEntry({
      institution:
        item.institution,

      location:
        locationText(item.location),

      study: [
        item.studyType,
        item.area
      ]
        .filter(Boolean)
        .join(" in "),

      date:
        dateRange(item),

      highlights:
        notes
    });
  });
}

/*
|--------------------------------------------------------------------------
| WORK
|--------------------------------------------------------------------------
*/

function renderWork(items = [], title = "Work") {
  return entrySection(title, items, item =>
    roleEntry({
      role:
        item.position ||
        item.name,

      organization:
        item.name ||
        item.organization,

      date:
        dateRange(item),

      location:
        locationText(
          item.location
        ),

      summary:
        item.summary,

      highlights:
        item.highlights
    })
  );
}

/*
|--------------------------------------------------------------------------
| VOLUNTEER
|--------------------------------------------------------------------------
*/

function renderVolunteer(items = [], title = "Volunteer") {
  return entrySection(title, items, item =>
    roleEntry({
      role:
        item.position ||
        item.organization,

      organization:
        item.organization,

      date:
        dateRange(item),

      location:
        locationText(
          item.location
        ),

      summary:
        item.summary,

      highlights:
        item.highlights
    })
  );
}

/*
|--------------------------------------------------------------------------
| PROJECTS
|--------------------------------------------------------------------------
|
| Mimics:
|
| Gitlytics | Python, Flask, React, PostgreSQL, Docker
|                                      June 2020 -- Present
|
|--------------------------------------------------------------------------
*/

function renderProjects(items = [], title = "Projects") {
  return entrySection(title, items, item => {
    const extras = [];

    if (
      Array.isArray(item.roles) &&
      item.roles.length
    ) {
      extras.push(
        `Role: ${item.roles.join(", ")}`
      );
    }

    if (item.entity) {
      extras.push(
        item.entity
      );
    }

    if (item.type) {
      extras.push(
        item.type
      );
    }

    return projectEntry({
      name:
        item.name,

      /*
       * You may use either:
       *
       * "technologies": [...]
       *
       * or standard JSON Resume:
       *
       * "keywords": [...]
       */
      keywords:
        arrayOrEmpty(
          item.technologies
        ).length
          ? item.technologies
          : item.keywords,

      date:
        dateRange(item),

      detail:
        extras.join(" | "),

      url:
        item.url,

      urlLabel:
        item.urlLabel ||
        "Project Link",

      summary:
        item.description,

      highlights:
        item.highlights
    });
  });
}

/*
|--------------------------------------------------------------------------
| AWARDS
|--------------------------------------------------------------------------
*/

function renderAwards(items = [], title = "Awards") {
  return entrySection(title, items, item =>
    creditEntry({
      name:
        item.title,

      date:
        singleDate(item),

      detail:
        item.awarder,

      highlights:
        item.summary
          ? [item.summary]
          : item.highlights
    })
  );
}

/*
|--------------------------------------------------------------------------
| CERTIFICATES
|--------------------------------------------------------------------------
*/

function renderCertificates(items = [], title = "Certifications") {
  return entrySection(title, items, item =>
    creditEntry({
      name:
        item.name,

      date:
        singleDate(item),

      detail:
        item.issuer,

      url:
        item.url,

      urlLabel:
        item.urlLabel ||
        "Credential",

      highlights:
        item.highlights
    })
  );
}

/*
|--------------------------------------------------------------------------
| PUBLICATIONS
|--------------------------------------------------------------------------
*/

function renderPublications(items = [], title = "Publications") {
  return entrySection(title, items, item =>
    creditEntry({
      name:
        item.name,

      date:
        singleDate(
          item,
          "releaseDate"
        ),

      detail:
        item.publisher,

      url:
        item.url,

      urlLabel:
        item.urlLabel ||
        "Publication Link",

      highlights:
        item.summary
          ? [item.summary]
          : item.highlights
    })
  );
}

/*
|--------------------------------------------------------------------------
| SKILLS
|--------------------------------------------------------------------------
*/

function renderSkills(items = [], title = "Skills") {
  return labelSection(title, items, skill =>
    labelLine(
      skill.name || "Skill",
      [
        skill.level,

        arrayOrEmpty(
          skill.keywords
        ).join(", "),

        skill.summary
      ]
    )
  );
}

/*
|--------------------------------------------------------------------------
| LANGUAGES
|--------------------------------------------------------------------------
*/

function renderLanguages(items = [], title = "Languages") {
  return labelSection(title, items, lang =>
    labelLine(
      lang.language || "Language",
      [
        lang.fluency,

        ...arrayOrEmpty(
          lang.keywords
        )
      ]
    )
  );
}

/*
|--------------------------------------------------------------------------
| INTERESTS
|--------------------------------------------------------------------------
*/

function renderInterests(items = [], title = "Interests") {
  return labelSection(title, items, item =>
    labelLine(
      item.name || "Interest",
      [
        arrayOrEmpty(
          item.keywords
        ).join(", ")
      ]
    )
  );
}

/*
|--------------------------------------------------------------------------
| REFERENCES
|--------------------------------------------------------------------------
*/

function renderReferences(items = [], title = "References") {
  return entrySection(title, items, item =>
    creditEntry({
      name:
        item.name ||
        "Reference",

      detail: joinMeta([
        item.position,
        item.organization,
        item.email,
        item.phone
      ]),

      note:
        item.reference
    })
  );
}


/*
|--------------------------------------------------------------------------
| SECTION ORDER AND TITLES
|--------------------------------------------------------------------------
|
| Every visible section maps a top-level resume key to its renderer.
| The array order below is the default layout.
|
| Both the order and the heading text can be overridden per resume:
|
| "meta": {
|   "order": ["education", "work", "projects", "skills"],
|   "aliases": { "work": "Experience", "volunteer": "Activities" }
| }
|
| Keys listed in meta.order render first, in that order. Any known
| section left out is appended afterwards in default order, so a
| partial list only promotes sections rather than hiding them.
| Unknown keys and duplicates are ignored.
|
| meta.aliases replaces a section's built-in heading. Each renderer
| keeps its default title as a parameter default, so an alias is
| simply the title argument being supplied. Aliases for unknown keys,
| and values that are not a non-empty string, are ignored.
|
|--------------------------------------------------------------------------
*/

const SECTIONS = [
  { key: "education", render: renderEducation },
  { key: "work", render: renderWork },
  { key: "volunteer", render: renderVolunteer },
  { key: "projects", render: renderProjects },
  { key: "awards", render: renderAwards },
  { key: "certificates", render: renderCertificates },
  { key: "publications", render: renderPublications },
  { key: "skills", render: renderSkills },
  { key: "languages", render: renderLanguages },
  { key: "interests", render: renderInterests },
  { key: "references", render: renderReferences }
];

function orderedSectionKeys(order) {
  const known = new Set(
    SECTIONS.map(s => s.key)
  );

  const keys = [];

  for (const key of arrayOrEmpty(order)) {
    if (
      known.has(key) &&
      !keys.includes(key)
    ) {
      keys.push(key);
    }
  }

  for (const { key } of SECTIONS) {
    if (!keys.includes(key)) {
      keys.push(key);
    }
  }

  return keys;
}

/*
 * Resolves the heading for one section.
 *
 * Returns undefined when no usable alias
 * exists, which lets the renderer fall
 * back to its own default title.
 */
function aliasTitle(aliases, key) {
  const alias =
    aliases &&
    typeof aliases === "object"
      ? aliases[key]
      : undefined;

  if (typeof alias !== "string") {
    return undefined;
  }

  const trimmed = alias.trim();

  return trimmed || undefined;
}

function renderSections(resume = {}, meta = {}) {
  const byKey = new Map(
    SECTIONS.map(s => [s.key, s.render])
  );

  return orderedSectionKeys(meta.order)
    .map(key =>
      byKey.get(key)(
        resume[key] || [],
        aliasTitle(meta.aliases, key)
      )
    )
    .join("");
}

/*
|--------------------------------------------------------------------------
| META
|--------------------------------------------------------------------------
|
| meta is not displayed as a visible resume section.
| It is used for HTML document metadata.
|
|--------------------------------------------------------------------------
*/

function renderMetaHead(meta = {}) {
  const tags = [];

  if (meta.canonical) {
    tags.push(
      `<link rel="canonical" href="${esc(
        normalizeUrl(
          meta.canonical
        )
      )}">`
    );
  }

  if (meta.lastModified) {
    tags.push(
      `<meta name="last-modified" content="${esc(
        meta.lastModified
      )}">`
    );
  }

  if (meta.version) {
    tags.push(
      `<meta name="resume-version" content="${esc(
        meta.version
      )}">`
    );
  }

  return tags.join("\n  ");
}

/*
|--------------------------------------------------------------------------
| MAIN RENDER
|--------------------------------------------------------------------------
*/

export function render(resume = {}) {
  const title =
    resume.basics?.name
      ? `${resume.basics.name} - Resume`
      : "Resume";

  const meta =
    resume.meta || {};

  const body = [
    renderHeader(
      resume.basics || {}
    ),

    renderSections(resume, meta)
  ].join("");

  return `<!doctype html>

<html lang="${esc(
    meta.language || "en"
  )}">

<head>

  <meta charset="utf-8">

  <meta
    name="viewport"
    content="width=device-width, initial-scale=1"
  >

  <meta
    name="generator"
    content="jsonresume-theme-jake-latex"
  >

  ${renderMetaHead(meta)}

  <title>
    ${esc(title)}
  </title>

  <style>
    ${css}
  </style>

</head>

<body>

  <main class="resume">
    ${body}
  </main>

</body>

</html>`;
}

export default {
  render
};