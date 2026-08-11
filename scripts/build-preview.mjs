import fs from "node:fs";
import { render } from "../index.js";
const resume = JSON.parse(fs.readFileSync(new URL("../resume.json", import.meta.url), "utf8"));
fs.writeFileSync(new URL("../preview.html", import.meta.url), render(resume));
console.log("Wrote preview.html");
