const css = [
  '@page{size:letter;margin:.48in .55in}',
  '*{box-sizing:border-box}',
  'html,body{margin:0;padding:0;background:#fff;color:#000}',
  'body{font-family:"Latin Modern Roman","CMU Serif","Computer Modern","Times New Roman",Times,serif;font-size:11pt;line-height:1.16;-webkit-print-color-adjust:exact;print-color-adjust:exact}',
  '.resume{width:100%;max-width:8.5in;margin:0 auto}',
  '.header{margin:0 0 10px;text-align:center}',
  '.name{margin:0 0 4px;font-size:25pt;line-height:1;font-weight:700;font-variant:small-caps;letter-spacing:.2px}',
  '.label{margin:0 0 3px;font-size:10pt;font-style:italic}',
  '.contact{font-size:9.4pt;line-height:1.25}',
  '.contact a,.inline-link{color:inherit;text-decoration:underline;text-underline-offset:1px}',
  '.sep{padding:0 4px}.summary{margin:5px 0 0;font-size:9.7pt;text-align:left}',
  '.section{margin:7px 0 0;break-inside:auto}',
  '.section-title{margin:0 0 5px;padding:0 0 2px;border-bottom:.8px solid #000;font-size:12pt;line-height:1.05;font-weight:400;font-variant:small-caps;letter-spacing:.35px}',
  '.entries{margin:0;padding:0 0 0 .15in;list-style:none}.entry{margin:0 0 6px;break-inside:avoid}',
  '.entry:last-child,.bullets li:last-child,.compact-line:last-child{margin-bottom:0}',
  '.row{display:grid;grid-template-columns:minmax(0,1fr) auto;column-gap:16px;align-items:baseline}',
  '.primary{min-width:0;font-weight:700}.meta-left,.meta-right,.project-tech{font-size:9.7pt;font-style:italic}',
  '.right{text-align:right;white-space:nowrap}.meta-row{margin-top:1px}.project-title{min-width:0;font-size:9.7pt}',
  '.bullets{margin:3px 0 0 .21in;padding:0 0 0 .16in}.bullets li{margin:0 0 2px;padding-left:1px;font-size:9.7pt}',
  '.plain-note{margin:3px 0 0;font-size:9.7pt}.compact-lines{margin:1px 0 0;padding:0 0 0 .15in;list-style:none;font-size:9.7pt}',
  '.compact-line{margin:0 0 3px}.compact-label{font-weight:700}',
  '@media print{.resume{max-width:none}a{color:#000}}'
].join('');

function esc(value) {
  return String(value || '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#39;');
}

function list(value) { return Array.isArray(value) ? value : []; }

function url(value) {
  if (!value || /^(https?:|mailto:|tel:)/i.test(value)) return value || '';
  return 'https://' + value;
}

function link(href, label) {
  return href && label ? '<a class="inline-link" href="' + esc(url(href)) + '">' + esc(label) + '</a>' : esc(label || '');
}

function monthYear(value) {
  if (!value) return '';
  const match = String(value).match(/^(\d{4})(?:-(\d{2}))?/);
  if (!match) return String(value);
  const months = ['Jan.', 'Feb.', 'Mar.', 'Apr.', 'May', 'Jun.', 'Jul.', 'Aug.', 'Sep.', 'Oct.', 'Nov.', 'Dec.'];
  const month = Number(match[2]);
  return month > 0 && month < 13 ? months[month - 1] + ' ' + match[1] : match[1];
}

function dates(item) {
  const start = monthYear(item.startDate);
  const end = monthYear(item.endDate) || (start ? 'Present' : '');
  return [start, end].filter(Boolean).join(' -- ');
}

function location(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return '';
  return [value.address, value.city, value.region, value.postalCode, value.countryCode].filter(Boolean).join(', ');
}

function bullet(values) {
  const items = list(values).filter(Boolean);
  return items.length ? '<ul class="bullets">' + items.map(value => '<li>' + esc(value) + '</li>').join('') + '</ul>' : '';
}

function item(options) {
  const title = options.titleHtml || esc(options.title || '');
  const subtitle = options.subtitleHtml || esc(options.subtitle || '');
  const meta = options.subtitle || options.subtitleHtml || options.rightBottom;
  return '<li class="entry"><div class="row"><div class="primary">' + title + '</div><div class="right">' + esc(options.rightTop || '') + '</div></div>' +
    (meta ? '<div class="row meta-row"><div class="meta-left">' + subtitle + '</div><div class="meta-right right">' + esc(options.rightBottom || '') + '</div></div>' : '') +
    (options.note ? '<div class="plain-note">' + esc(options.note) + '</div>' : '') + bullet(options.highlights) + '</li>';
}

function section(title, body) {
  return body ? '<section class="section"><h2 class="section-title">' + esc(title) + '</h2>' + body + '</section>' : '';
}

function entries(title, values, renderer) {
  const items = list(values);
  return items.length ? section(title, '<ul class="entries">' + items.map(renderer).join('') + '</ul>') : '';
}

function lines(title, values, renderer) {
  const items = list(values);
  return items.length ? section(title, '<ul class="compact-lines">' + items.map(renderer).join('') + '</ul>') : '';
}

function line(label, values) {
  const detail = list(values).filter(Boolean).join('; ');
  return '<li class="compact-line"><span class="compact-label">' + esc(label) + '</span>' + (detail ? ': ' + esc(detail) : '') + '</li>';
}

function header(basics) {
  const contacts = [];
  const place = location(basics.location);
  if (place) contacts.push(esc(place));
  if (basics.phone) contacts.push(link('tel:' + basics.phone, basics.phone));
  if (basics.email) contacts.push(link('mailto:' + basics.email, basics.email));
  list(basics.profiles).forEach(profile => {
    const label = profile.network || profile.username || profile.url;
    if (label && profile.url) contacts.push(link(profile.url, label));
  });
  if (basics.url) contacts.push(link(basics.url, basics.url));
  return '<header class="header"><h1 class="name">' + esc(basics.name || '') + '</h1>' +
    (basics.label ? '<div class="label">' + esc(basics.label) + '</div>' : '') +
    (contacts.length ? '<div class="contact">' + contacts.join('<span class="sep">|</span>') + '</div>' : '') +
    (basics.summary ? '<div class="summary">' + esc(basics.summary) + '</div>' : '') + '</header>';
}

function education(values) {
  return entries('Education', values, value => {
    const notes = [];
    if (list(value.courses).length) notes.push('Relevant Coursework: ' + value.courses.join(', '));
    if (value.score) notes.push('GPA: ' + value.score);
    return item({ title: value.institution, titleHtml: value.url ? link(value.url, value.institution || value.url) : '', rightTop: dates(value), subtitle: [value.studyType, value.area].filter(Boolean).join(' in '), highlights: notes });
  });
}

function work(values) {
  return entries('Work', values, value => item({ title: value.position || value.name, rightTop: dates(value), subtitle: value.name, subtitleHtml: value.url ? link(value.url, value.name || value.url) : '', rightBottom: value.location, note: [value.description, value.summary].filter(Boolean).join(' -- '), highlights: value.highlights }));
}

function volunteer(values) {
  return entries('Volunteer', values, value => item({ title: value.position || value.organization, rightTop: dates(value), subtitle: value.organization, subtitleHtml: value.url ? link(value.url, value.organization || value.url) : '', note: value.summary, highlights: value.highlights }));
}

function projects(values) {
  return entries('Projects', values, value => {
    const keywords = list(value.keywords).filter(Boolean).join(', ');
    const title = '<div class="project-title"><strong>' + esc(value.name || '') + '</strong>' + (keywords ? ' <span>|</span> <span class="project-tech">' + esc(keywords) + '</span>' : '') + '</div>';
    return item({ titleHtml: title, rightTop: dates(value), subtitle: [list(value.roles).filter(Boolean).join(', '), value.entity, value.type].filter(Boolean).join(' | '), subtitleHtml: value.url ? link(value.url, 'Project') : '', note: value.description, highlights: value.highlights });
  });
}

function awards(values) { return entries('Awards', values, value => item({ title: value.title, rightTop: monthYear(value.date), subtitle: value.awarder, note: value.summary })); }
function certificates(values) { return entries('Certificates', values, value => item({ title: value.name, rightTop: monthYear(value.date), subtitle: value.issuer, subtitleHtml: value.url ? [esc(value.issuer || ''), link(value.url, 'Credential')].filter(Boolean).join(' | ') : '' })); }
function publications(values) { return entries('Publications', values, value => item({ title: value.name, rightTop: monthYear(value.releaseDate), subtitle: value.publisher, subtitleHtml: value.url ? [esc(value.publisher || ''), link(value.url, 'Publication')].filter(Boolean).join(' | ') : '', note: value.summary })); }
function skills(values) { return lines('Skills', values, value => line(value.name || 'Skill', [value.level, list(value.keywords).join(', ')])); }
function languages(values) { return lines('Languages', values, value => line(value.language || 'Language', [value.fluency])); }
function interests(values) { return lines('Interests', values, value => line(value.name || 'Interest', [list(value.keywords).join(', ')])); }
function references(values) { return entries('References', values, value => item({ title: value.name || 'Reference', note: value.reference })); }

const sections = [['education', education], ['work', work], ['volunteer', volunteer], ['projects', projects], ['awards', awards], ['certificates', certificates], ['publications', publications], ['skills', skills], ['languages', languages], ['interests', interests], ['references', references]];

export function render(resume) {
  const value = resume || {};
  const basics = value.basics || {};
  const meta = value.meta || {};
  const tags = [];
  if (meta.canonical) tags.push('<link rel="canonical" href="' + esc(url(meta.canonical)) + '">');
  if (meta.lastModified) tags.push('<meta name="last-modified" content="' + esc(meta.lastModified) + '">');
  if (meta.version) tags.push('<meta name="resume-version" content="' + esc(meta.version) + '">');
  const body = [header(basics)].concat(sections.map(pair => pair[1](value[pair[0]]))).join('');
  const title = basics.name ? basics.name + ' - Resume' : 'Resume';
  return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="generator" content="jsonresume-theme-jake-resume">' + tags.join('') + '<title>' + esc(title) + '</title><style>' + css + '</style></head><body><main class="resume">' + body + '</main></body></html>';
}

export default { render };
