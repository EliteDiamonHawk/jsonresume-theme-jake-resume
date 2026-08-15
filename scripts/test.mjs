import fs from "node:fs";
import assert from "node:assert/strict";
import { render } from "../index.js";
const resume = JSON.parse(fs.readFileSync(new URL("../resume.json", import.meta.url), "utf8"));
const html = render(resume, { censor: false });
assert.match(html, /Maya Chen/);
assert.match(html, /Education/);
assert.match(html, /Experience/);
assert.match(html, /Certifications/);
assert.match(html, /Skills/);
assert.match(html, /Activities/);
assert.match(html, /<style>/);
assert.doesNotMatch(html, /@media screen/);
assert.doesNotMatch(html, /#ececec/);
assert.ok(html.length > 5000);

// Censorship: meta.censorship hides listed basics fields and profiles.
const censored = render(resume, { censor: true });
assert.doesNotMatch(censored, /maya\.chen@example\.com/);
assert.doesNotMatch(censored, /555-0187/);
assert.doesNotMatch(censored, /kaggle/i);
assert.doesNotMatch(censored, /linkedin/i);
assert.match(censored, /Maya Chen/);
assert.match(censored, /github\.com\/maya-codes/);
assert.match(censored, /Oakland, CA, US/);
assert.match(censored, /Experience/);

// Locations are plain strings; object-style values are intentionally ignored.
const stringLocation = render({
  basics: { name: "Location Test", location: "Oakland, CA, US" }
});
assert.match(stringLocation, /Oakland, CA, US/);

const objectLocation = render({
  basics: { name: "Location Test", location: { city: "Oakland" } }
});
assert.doesNotMatch(objectLocation, /Oakland/);

// Certificate URLs use a default label unless urlLabel is supplied.
const certificateLinks = render({
  certificates: [
    { name: "Default", issuer: "Issuer", url: "example.com/default" },
    { name: "Custom", issuer: "Issuer", url: "example.com/custom", urlLabel: "Verify" }
  ]
});
assert.match(certificateLinks, />Credential<|>Credential\s*</);
assert.match(certificateLinks, />Verify<|>Verify\s*</);
assert.match(certificateLinks, /href="https:\/\/example\.com\/default"/);

// A resume without meta.censorship is never censored.
const { censorship, ...metaWithout } = resume.meta;
const uncensored = render({ ...resume, meta: metaWithout });
assert.match(uncensored, /maya\.chen@example\.com/);
assert.match(uncensored, /Kaggle/);

// toggle: false is respected without an explicit override.
const off = render({
  ...resume,
  meta: { ...resume.meta, censorship: { ...censorship, toggle: false } }
});
assert.match(off, /maya\.chen@example\.com/);

// Default render follows the resume's own toggle.
assert.equal(render(resume), censored);

console.log("Theme render test passed");
