import { illustrations } from "./illustrations";

// Order of the project pages, used for the previous / next navigation.
export const projects = [
  { slug: "solarconflux", title: "SolarConflux", illustration: illustrations.solarconflux },
  { slug: "lunar-spaceport", title: "Lunar Spaceport", illustration: illustrations.lunarSpaceport },
  { slug: "ypsat", title: "YPSat", illustration: illustrations.ypsat },
  { slug: "phobos-deimos", title: "Phobos & Deimos", illustration: illustrations.phobosDeimos },
  { slug: "ceres", title: "Diplona", illustration: illustrations.diplona },
] as const;

export type ProjectSlug = (typeof projects)[number]["slug"];
