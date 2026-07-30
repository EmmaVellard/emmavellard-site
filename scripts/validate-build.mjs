import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const outputRoot = path.resolve("dist");

if (!fs.existsSync(outputRoot)) {
  console.error("dist/ does not exist. Run the production build first.");
  process.exit(1);
}

const walk = (directory) =>
  fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const entryPath = path.join(directory, entry.name);
    return entry.isDirectory() ? walk(entryPath) : [entryPath];
  });

const htmlFiles = walk(outputRoot).filter((file) => file.endsWith(".html"));
const errors = [];

const resolveInternalTarget = (href) => {
  const pathname = href.split(/[?#]/, 1)[0];
  if (!pathname || pathname === "/") return path.join(outputRoot, "index.html");
  if (path.extname(pathname)) return path.join(outputRoot, pathname);
  return path.join(outputRoot, pathname.replace(/\/$/, ""), "index.html");
};

for (const file of htmlFiles) {
  const html = fs.readFileSync(file, "utf8");
  const relativePath = path.relative(outputRoot, file);

  const h1Count = (html.match(/<h1\b/gi) ?? []).length;
  if (h1Count !== 1) errors.push(`${relativePath}: expected one h1, found ${h1Count}`);

  const ids = [...html.matchAll(/\sid="([^"]+)"/g)].map((match) => match[1]);
  const duplicateIds = [...new Set(ids.filter((id, index) => ids.indexOf(id) !== index))];
  if (duplicateIds.length) errors.push(`${relativePath}: duplicate IDs ${duplicateIds.join(", ")}`);

  for (const match of html.matchAll(/<img\b[^>]*>/gi)) {
    const image = match[0];
    if (!/\salt="[^"]*"/i.test(image)) errors.push(`${relativePath}: image without alt text`);
    if (!/\swidth="\d+"/i.test(image) || !/\sheight="\d+"/i.test(image)) {
      errors.push(`${relativePath}: image without intrinsic dimensions`);
    }
  }

  for (const match of html.matchAll(/href="(\/[^"#]*)[^\"]*"/g)) {
    const target = resolveInternalTarget(match[1]);
    if (!fs.existsSync(target)) errors.push(`${relativePath}: missing internal target ${match[1]}`);
  }

  const idSet = new Set(ids);
  for (const nav of html.matchAll(/<nav[^>]*data-section-nav[^>]*>([\s\S]*?)<\/nav>/g)) {
    for (const match of nav[1].matchAll(/href="#([^"]+)"/g)) {
      if (!idSet.has(match[1])) errors.push(`${relativePath}: missing section #${match[1]}`);
    }
  }

  for (const match of html.matchAll(/<a\b[^>]*target="_blank"[^>]*>/gi)) {
    if (!/\srel="[^"]*noopener[^"]*"/i.test(match[0])) {
      errors.push(`${relativePath}: new-tab link without rel=noopener`);
    }
  }

  const footerCount = (html.match(/<footer\b/gi) ?? []).length;
  const expectedFooters = relativePath === "index.html" ? 0 : 1;
  if (footerCount !== expectedFooters) {
    errors.push(`${relativePath}: expected ${expectedFooters} footer, found ${footerCount}`);
  }
}

if (errors.length) {
  console.error(errors.join("\n"));
  process.exit(1);
}

console.log(
  `Validated ${htmlFiles.length} pages: structure, assets, links, section navigation, and footers.`,
);
