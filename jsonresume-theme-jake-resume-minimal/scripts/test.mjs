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

console.log("Minimal theme render test passed");
