// Exact counts transcribed from the supplied DPS poster; no model rerun or digitisation.
import fs from "node:fs/promises";
import crypto from "node:crypto";
const poster = await fs.readFile("public/files/posters/VELLARD_PosterDPS58.pdf");
const tides = await fs.readFile("data/lunar/dps-2026-tides.csv");
const families = [
  { name: "Homogeneous", count: 7, light: "#2a62b8", dark: "#8fc6e3" },
  { name: "Layered", count: 5, light: "#397b83", dark: "#7acec8" },
  { name: "FeO-rich", count: 7, light: "#83649e", dark: "#c5a7e8" },
];
await fs.mkdir("public/images/research", { recursive: true });
await fs.mkdir("docs", { recursive: true });
const provenance = {
  source: "/files/posters/VELLARD_PosterDPS58.pdf",
  source_sha256: crypto.createHash("sha256").update(poster).digest("hex"),
  source_panels: [2, 6, 9],
  mass_matching_interiors: 1425,
  admissible_interiors: 19,
  admissibility: "Mass, moment of inertia and core radius; not an all-observations fit",
  mantle_families: families.map(({ name, count }) => ({ name, count })),
  grail_degree_1_matches: 2,
  grail_degree_1_and_apollo_heat_flow_matches: 0,
  scope: "Only the compositions, assumptions and prescribed temperature fields tested in this poster.",
  tidal_figure: {
    files: [
      "/images/research/grail-tidal-response-light.svg",
      "/images/research/grail-tidal-response-dark.svg",
    ],
    method:
      "Panel 6 redrawn from 76 original values, 19 elastic interiors × 4 orders. Transparent SVG; no digitisation or model rerun.",
    pinned_data: "data/lunar/dps-2026-tides.csv",
    pinned_data_sha256: crypto.createHash("sha256").update(tides).digest("hex"),
    original_data: "lunar-bsm-interior-models/results/dps_2026_followup/N4/G1_19_4PI/G1_APPARENT_K3M.csv",
    original_generator:
      "lunar-bsm-interior-models/conference/preparation_2026-10-08/make_poster_v41_figures.py",
    quantity: "k_ts_PM+XM_intercept, K_set=ELASTIC; time-variable tide, 2012 GRAIL orbit",
    park_error_bars: "±15 × formal uncertainty, as in panel 6; not labelled as 1σ",
    scope: "Range overlap separately in each order is not a simultaneous fit by one model.",
  },
};
await fs.writeFile("docs/dps-2026-figure-provenance.json", JSON.stringify(provenance, null, 2) + "\n");
for (const theme of ["light", "dark"]) {
  const ink = theme === "light" ? "#0d2140" : "#e6eef9";
  const muted = theme === "light" ? "#44597a" : "#9fb2cc";
  const line = theme === "light" ? "#b8cce2" : "#33455e";
  let x = 30;
  const bars = families
    .map((family) => {
      const width = (680 * family.count) / 19;
      const fill = family[theme];
      const element = `<rect x="${x}" y="177" width="${width}" height="42" fill="${fill}"/><text x="${x + width / 2}" y="204" text-anchor="middle" fill="${theme === "light" ? "#ffffff" : "#07111f"}" font-size="21" font-weight="600">${family.count}</text>`;
      x += width;
      return element;
    })
    .join("");
  const legend = families
    .map(
      (family, index) =>
        `<rect x="${30 + index * 230}" y="247" width="12" height="12" rx="2" fill="${family[theme]}"/><text x="${50 + index * 230}" y="258" font-size="17" fill="${muted}">${family.name}</text>`,
    )
    .join("");
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="740" height="300" viewBox="0 0 740 300" role="img" aria-labelledby="title desc"><title id="title">19 of 1,425 lunar interiors satisfy mass, moment of inertia and core-radius constraints</title><desc id="desc">The 19 retained interiors comprise 7 homogeneous, 5 layered and 7 FeO-rich mantles. Counts from panel 2 of the DPS 2026 poster.</desc><g font-family="Arial, sans-serif"><text x="30" y="67" fill="${ink}" font-size="46" font-weight="600">1,425</text><text x="30" y="100" fill="${muted}" font-size="18">Mass-matching interiors</text><path d="M290 60 H380 l-10 -7 M380 60 l-10 7" fill="none" stroke="${muted}" stroke-width="2"/><text x="425" y="67" fill="${ink}" font-size="46" font-weight="600">19</text><text x="425" y="100" fill="${muted}" font-size="18">Also match moment of inertia</text><text x="425" y="125" fill="${muted}" font-size="18">and core radius</text><line x1="30" x2="710" y1="148" y2="148" stroke="${line}"/><text x="30" y="166" fill="${muted}" font-size="13">THE 19 RETAINED INTERIORS</text>${bars}${legend}</g></svg>`;
  await fs.writeFile(`public/images/research/model-selection-${theme}.svg`, svg);
}
console.log("Built two theme variants and exact-count provenance for the lunar results proposal.");
