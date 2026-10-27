// One-off asset preparation; run after a build. This is not part of the site build.
import fs from "node:fs/promises";
import path from "node:path";
import sharp from "sharp";

const root = process.cwd();
const walk = async (directory) =>
  (
    await Promise.all(
      (await fs.readdir(directory, { withFileTypes: true })).map(async (entry) => {
        const name = path.join(directory, entry.name);
        return entry.isDirectory() ? walk(name) : [name];
      }),
    )
  ).flat();
const sources = new Set();
for (const file of (await walk(path.join(root, "dist"))).filter((file) => file.endsWith(".html"))) {
  const html = await fs.readFile(file, "utf8");
  for (const match of html.matchAll(/<img\b[^>]*\bsrc="(\/images\/[^"?]+\.webp)"/g)) sources.add(match[1]);
}
const sizes = new Map([
  ["/images/accents/contact.webp", 192],
  ["/images/accents/research-interior.webp", 192],
  ["/images/accents/back-to-top.webp", 192],
  ["/images/accents/footer-explorer.webp", 384],
]);
let before = 0,
  after = 0,
  count = 0;
for (const source of sources) {
  const filename = path.join(root, "public", source);
  const original = await fs.readFile(filename);
  let pipeline = sharp(original);
  if (sizes.has(source))
    pipeline = pipeline.resize(sizes.get(source), sizes.get(source), {
      fit: "inside",
      withoutEnlargement: true,
    });
  const encoded = await pipeline.webp({ quality: 86, alphaQuality: 90, effort: 6 }).toBuffer();
  before += original.length;
  if (encoded.length < original.length) {
    await fs.writeFile(filename, encoded);
    count++;
    after += encoded.length;
  } else after += original.length;
}
console.log(
  JSON.stringify({
    filesOptimized: count,
    beforeBytes: before,
    afterBytes: after,
    reductionPercent: Math.round((1 - after / before) * 100),
  }),
);
