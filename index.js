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

.contact {
  font-size: 9.4pt;
  line-height: 1.25;
}

.contact a {
  color: inherit;
  text-decoration: underline;
  text-underline-offset: 1px;
}

.sep { padding: 0 4px; }

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

.entry:last-child { margin-bottom: 0; }

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

.meta-row { margin-top: 1px; }

.bullets {
  margin: 3px 0 0 0.21in;
  padding: 0 0 0 0.16in;
}

.bullets li {
  margin: 0 0 2px;
  padding-left: 1px;
  font-size: 9.7pt;
}

.bullets li:last-child { margin-bottom: 0; }

.skills {
  margin: 1px 0 0;
  padding: 0 0 0 0.15in;
  list-style: none;
  font-size: 9.7pt;
}

.skill-line { margin: 0 0 3px; }
.skill-line:last-child { margin-bottom: 0; }
.skill-label { font-weight: 700; }

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
  .resume { max-width: none; }
  a { color: #000; }
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
  if (/^(https?:|mailto:|tel:)/i.test(value)) return value;
  return `https://${value}`;
}

function monthYear(value) {
  if (!value) return "";
  const match = String(value).match(/^(\d{4})-(\d{2})/);
  if (!match) return String(value);
  const year = Number(match[1]);
  const month = Number(match[2]);
  if (month < 1 || month > 12) return String(value);
  const names = ["Jan.", "Feb.", "Mar.", "Apr.", "May", "Jun.", "Jul.", "Aug.", "Sep.", "Oct.", "Nov.", "Dec."];
  return `${names[month - 1]} ${year}`;
}

function dateRange(item = {}) {
  if (item.dateText) return item.dateText;
  const start = item.startDateText || monthYear(item.startDate);
  let end = item.endDateText || monthYear(item.endDate);
  if (!end && start) end = "Present";
  return [start, end].filter(Boolean).join(" -- ");
}

function locationText(location = {}) {
  if (typeof location === "string") return location;
  return [location.city, location.region].filter(Boolean).join(", ");
}

function bullets(items = []) {
  if (!Array.isArray(items) || !items.length) return "";
  return `<ul class="bullets">${items.map(x => `<li>${esc(x)}</li>`).join("")}</ul>`;
}

function entry({ title = "", rightTop = "", subtitle = "", rightBottom = "", highlights = [] }) {
  return `
    <li class="entry">
      <div class="row">
        <div class="primary">${esc(title)}</div>
        <div class="right">${esc(rightTop)}</div>
      </div>
      ${(subtitle || rightBottom) ? `<div class="row meta-row">
        <div class="meta-left">${esc(subtitle)}</div>
        <div class="meta-right right">${esc(rightBottom)}</div>
      </div>` : ""}
      ${bullets(highlights)}
    </li>`;
}

function section(title, body) {
  if (!body) return "";
  return `<section class="section"><h2 class="section-title">${esc(title)}</h2>${body}</section>`;
}

function renderHeader(basics = {}) {
  const location = locationText(basics.location);
  const contacts = [];
  if (location) contacts.push(esc(location));
  if (basics.phone) contacts.push(`<a href="${esc(`tel:${basics.phone}`)}">${esc(basics.phone)}</a>`);
  if (basics.email) contacts.push(`<a href="${esc(`mailto:${basics.email}`)}">${esc(basics.email)}</a>`);

  for (const profile of basics.profiles || []) {
    const label = profile.network || profile.username || profile.url;
    const href = profile.url;

    if (label && href) {
      contacts.push(
        `<a href="${esc(normalizeUrl(href))}">${esc(label)}</a>`
      );
    }
  }

  if (basics.url) contacts.push(`<a href="${esc(normalizeUrl(basics.url))}">${esc(basics.url)}</a>`);

  return `<header class="header">
    <h1 class="name">${esc(basics.name || "")}</h1>
    <div class="contact">${contacts.join('<span class="sep">|</span>')}</div>
  </header>`;
}

function renderEducation(items = []) {
  if (!items.length) return "";
  const html = items.map(item => {
    const study = [item.studyType, item.area].filter(Boolean).join(" in ");
    const notes = [];
    if (Array.isArray(item.courses) && item.courses.length) notes.push(`Relevant Coursework: ${item.courses.join(", ")}`);
    if (item.score) notes.push(`GPA: ${item.score}`);
    if (Array.isArray(item.highlights)) notes.push(...item.highlights);
    return entry({
      title: item.institution,
      rightTop: locationText(item.location),
      subtitle: study,
      rightBottom: dateRange(item),
      highlights: notes
    });
  }).join("");
  return section("Education", `<ul class="entries">${html}</ul>`);
}

function renderWork(items = []) {
  if (!items.length) return "";
  const html = items.map(item => entry({
    title: item.position || item.name,
    rightTop: dateRange(item),
    subtitle: item.name || item.organization,
    rightBottom: locationText(item.location),
    highlights: item.highlights || []
  })).join("");
  return section("Experience", `<ul class="entries">${html}</ul>`);
}

function renderCertificates(items = []) {
  if (!items.length) return "";
  const html = items.map(item => entry({
    title: item.name,
    rightTop: item.dateText || monthYear(item.date),
    subtitle: item.issuer,
    rightBottom: "",
    highlights: item.highlights || []
  })).join("");
  return section("Certifications", `<ul class="entries">${html}</ul>`);
}

function renderSkills(resume = {}) {
  const lines = [];
  for (const lang of resume.languages || []) {
    const value = [lang.fluency, ...(lang.keywords || [])].filter(Boolean).join("; ");
    lines.push(`<li class="skill-line"><span class="skill-label">${esc(lang.language)}</span>: ${esc(value)}</li>`);
  }
  for (const skill of resume.skills || []) {
    const parts = [];
    if (skill.level) parts.push(skill.level);
    if (Array.isArray(skill.keywords) && skill.keywords.length) parts.push(skill.keywords.join(", "));
    if (skill.summary) parts.push(skill.summary);
    lines.push(`<li class="skill-line"><span class="skill-label">${esc(skill.name)}</span>: ${esc(parts.join("; "))}</li>`);
  }
  return lines.length ? section("Skills", `<ul class="skills">${lines.join("")}</ul>`) : "";
}

function renderActivities(items = []) {
  if (!items.length) return "";
  const html = items.map(item => entry({
    title: item.position || item.role || item.name,
    rightTop: dateRange(item),
    subtitle: item.organization || item.name,
    rightBottom: locationText(item.location),
    highlights: item.highlights || []
  })).join("");
  return section("Activities", `<ul class="entries">${html}</ul>`);
}

function renderProjects(items = []) {
  if (!items.length) return "";
  const html = items.map(item => entry({
    title: item.name,
    rightTop: dateRange(item),
    subtitle: (item.roles || []).join(", "),
    rightBottom: "",
    highlights: item.highlights || (item.description ? [item.description] : [])
  })).join("");
  return section("Projects", `<ul class="entries">${html}</ul>`);
}

export function render(resume = {}) {
  const title = resume.basics?.name ? `${resume.basics.name} - Resume` : "Resume";
  const body = [
    renderHeader(resume.basics),
    renderEducation(resume.education || []),
    renderWork(resume.work || []),
    renderProjects(resume.projects || []),
    renderCertificates(resume.certificates || []),
    renderSkills(resume),
    renderActivities(resume.activities || [])
  ].join("");

  return `<!doctype html>
<html lang="${esc(resume.meta?.language || "en")}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="generator" content="jsonresume-theme-jake-latex">
  <title>${esc(title)}</title>
  <style>${css}</style>
</head>
<body>
  <main class="resume">${body}</main>
</body>
</html>`;
}

export default { render };
