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
assert.equal(render(resume), html);

const standardLocation = render({ basics: { name: "Compatibility", location: { city: "Oakland" } } });
assert.match(standardLocation, /Oakland/);
assert.match(render({ basics: { name: "Location", location: "Oakland, CA" } }), /Oakland, CA/);

console.log("Extra theme render test passed");
