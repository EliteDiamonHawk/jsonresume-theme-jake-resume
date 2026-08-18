import fs from "node:fs";
import assert from "node:assert/strict";
import { render } from "../index.js";

const resume = JSON.parse(fs.readFileSync(new URL("../resume.json", import.meta.url), "utf8"));
const html = render(resume, { censor: false });
assert.match(html, /Maya Chen/);
assert.match(html, /Experience/);
assert.match(html, /Certifications/);
assert.match(html, /Activities/);

const censored = render(resume, { censor: true });
assert.doesNotMatch(censored, /maya\.chen@example\.com/);
assert.doesNotMatch(censored, /555-0187/);
assert.match(censored, /github\.com\/maya-codes/);
assert.equal(render(resume), censored);

const standardLocation = render({ basics: { name: "Compatibility", location: { city: "Oakland" } } });
assert.match(standardLocation, /Oakland/);
assert.match(render({ basics: { name: "Location", location: "Oakland, CA" } }), /Oakland, CA/);

for (const image of ["https://images.example.com/portrait.png", "http://images.example.com/portrait.jpeg", "https://images.example.com/portrait.svg"]) {
  const imageHtml = render({ basics: { name: "Image Test", image } });
  assert.match(imageHtml, /class="header with-image"/);
  assert.match(imageHtml, new RegExp(`src="${image.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}"`));
}
for (const image of ["portrait.png", "data:image/svg+xml,%3Csvg%3E%3C/svg%3E"]) {
  assert.doesNotMatch(render({ basics: { name: "Image Test", image } }), /class="header with-image"/);
}
assert.match(html, /object-fit: cover/);
assert.match(html, /beforeprint/);

console.log("Extra theme render test passed");
