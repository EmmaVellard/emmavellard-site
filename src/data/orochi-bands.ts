// Nominal band centres and full widths used in the 2023 internship report, Table 4 (p. 21).
// Rectangular intervals are a presentation of that table, not calibrated filter response curves.
export const orochiBands = [
  { name: "ul", centre: 0.39, width: 0.05 },
  { name: "b", centre: 0.48, width: 0.03 },
  { name: "v", centre: 0.55, width: 0.03 },
  { name: "d", centre: 0.65, width: 0.04 },
  { name: "e", centre: 0.73, width: 0.03 },
  { name: "x", centre: 0.86, width: 0.03 },
  { name: "p", centre: 0.95, width: 0.06 },
] as const;
