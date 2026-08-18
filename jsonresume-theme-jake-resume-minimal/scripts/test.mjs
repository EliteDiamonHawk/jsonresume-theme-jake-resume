import fs from "node:fs";
import assert from "node:assert/strict";
import { render } from "../index.js";

const resume = JSON.parse(fs.readFileSync(new URL("../resume.json", import.meta.url), "utf8"));
const html = render(resume);
assert.match(html, /Maya Chen/);
assert.match(html, /Education/);
assert.match(html, /Work/);
assert.match(html, /Certificates/);
assert.match(html, /Skills/);
assert.match(html, /Volunteer/);
assert.match(html, /<style>/);
assert.doesNotMatch(html, /@media screen/);
assert.doesNotMatch(html, /#ececec/);
assert.ok(html.length > 5000);

const objectLocation = render({ basics: { name: "Location Test", location: { city: "Oakland" } } });
assert.match(objectLocation, /Oakland/);

const certificateLinks = render({
  certificates: [
    { name: "Default", issuer: "Issuer", url: "example.com/default" },
    { name: "Another", issuer: "Issuer", url: "example.com/another" }
  ]
});
assert.match(certificateLinks, />Credential<|>Credential\s*</);
assert.match(certificateLinks, /href="https:\/\/example\.com\/default"/);

for (const image of ["https://images.example.com/portrait.png", "http://images.example.com/portrait.jpeg", "https://images.example.com/portrait.svg"]) {
  const imageHtml = render({ basics: { name: "Image Test", image } });
  assert.match(imageHtml, /class="header with-image"/);
  assert.match(imageHtml, new RegExp(`src="${image.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}"`));
}
for (const image of ["portrait.png", "data:image/svg+xml,%3Csvg%3E%3C/svg%3E"]) {
  assert.doesNotMatch(render({ basics: { name: "Image Test", image } }), /class="header with-image"/);
}
assert.match(html, /object-fit:cover/);
assert.match(html, /beforeprint/);

console.log("Minimal theme render test passed");
