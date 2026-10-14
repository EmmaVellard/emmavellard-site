import { expect, test } from "@playwright/test";

test("Back to top appears only when scrolling up and returns every page to its beginning", async ({
  page,
}) => {
  for (const path of [
    "/",
    "/research",
    "/projects/solarconflux",
    "/projects/lunar-spaceport",
    "/projects/ypsat",
    "/projects/phobos-deimos",
    "/projects/ceres",
  ]) {
    await page.goto(path);
    const button = page.getByRole("button", { name: "Back to top", exact: true });
    await expect(button).toBeHidden();
    await page.locator("footer").scrollIntoViewIfNeeded();
    await expect(button).toBeHidden();
    await page.mouse.wheel(0, -140);
    await expect(button).toBeVisible();
    await page.mouse.wheel(0, 60);
    await expect(button).toBeHidden();
    await page.mouse.wheel(0, -60);
    await expect(button).toBeVisible();
    await expect
      .poll(() =>
        button.locator("img").evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth > 0),
      )
      .toBeTruthy();
    await button.click();
    await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0);
    await expect(button).toBeHidden();
    await expect(page.locator("#main-content")).toBeFocused();
  }
});

test("Back to top works with the keyboard on a narrow dark screen and respects reduced motion", async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 740 });
  await page.emulateMedia({ colorScheme: "dark", reducedMotion: "reduce" });
  await page.goto("/projects/ypsat");
  await page.locator("footer").scrollIntoViewIfNeeded();
  const button = page.getByRole("button", { name: "Back to top", exact: true });
  await expect(button).toBeHidden();
  await page.evaluate(() => window.scrollBy({ top: -140, behavior: "instant" }));
  await expect(button).toBeVisible();
  const bounds = await button.boundingBox();
  expect(bounds!.x).toBeGreaterThanOrEqual(0);
  expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(320);
  expect(bounds!.y + bounds!.height).toBeLessThanOrEqual(740);
  expect(bounds!.width).toBeGreaterThanOrEqual(44);
  await button.focus();
  await button.press("Enter");
  expect(await page.evaluate(() => window.scrollY)).toBe(0);
  await expect(button).toBeHidden();
  await expect(page.locator("#main-content")).toBeFocused();
});

test("the homepage uses the brand as its home link and ends with the contact footer", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("link", { name: "Emma Vellard" })).toHaveAttribute("href", "/");
  await expect(page.locator("footer#contact")).toHaveCount(1);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Moon");
});

test("the navigation stays visible while scrolling", async ({ page }) => {
  await page.goto("/");
  await page.mouse.wheel(0, 2000);
  await expect(page.locator("#site-navbar")).toBeInViewport();
});

test("the theme toggle switches and remembers dark mode", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "light" });
  await page.goto("/");

  const html = page.locator("html");
  await expect(html).toHaveAttribute("data-theme", "light");

  await page.locator(".theme-toggle").click();
  await expect(html).toHaveAttribute("data-theme", "dark");
  await expect(page.locator(".theme-toggle")).toHaveAttribute("aria-label", "Switch to light mode");

  await page.reload();
  await expect(html).toHaveAttribute("data-theme", "dark");
});

test("the mobile menu opens, closes, and reports its state", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");

  const openMenu = page.locator(".nav-burger");
  await openMenu.click();
  await expect(openMenu).toHaveAttribute("aria-expanded", "true");
  await expect(openMenu).toHaveAttribute("aria-label", "Close menu");

  await page.locator(".mobile-close").click();
  await expect(openMenu).toHaveAttribute("aria-expanded", "false");
  await expect(openMenu).toHaveAttribute("aria-label", "Open menu");
});

test("the mobile menu covers the viewport with an opaque panel in both themes", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ colorScheme: "light" });
  await page.goto("/#path");
  for (const theme of ["light", "dark"]) {
    if (theme === "dark")
      await page.getByRole("button", { name: "Switch to dark mode", exact: true }).click();
    await page.getByRole("button", { name: "Open menu", exact: true }).click();
    const overlay = page.locator("#mobile-menu");
    const panel = page.getByRole("dialog", { name: "Menu", exact: true });
    await expect(overlay).toHaveCSS("opacity", "1");
    const rect = await overlay.boundingBox();
    expect(rect!.x).toBe(0);
    expect(rect!.y).toBe(0);
    expect(rect!.width).toBe(390);
    expect(rect!.height).toBe(844);
    await expect(panel).toHaveCSS(
      "background-color",
      theme === "light" ? "rgb(238, 245, 252)" : "rgb(7, 17, 31)",
    );
    await expect(page.locator("#site-navbar")).toHaveCSS(
      "background-color",
      theme === "light" ? "rgb(238, 245, 252)" : "rgb(7, 17, 31)",
    );
    const lastLink = panel.getByRole("link", { name: "Download CV", exact: true });
    await expect(lastLink).toBeInViewport();
    await page.keyboard.press("Escape");
    await expect(panel).toBeHidden();
    await expect(page.getByRole("button", { name: "Open menu", exact: true })).toBeFocused();
  }
});

test("opening the mobile menu near the bottom preserves the page and sticky navbar", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.locator("footer").scrollIntoViewIfNeeded();
  const before = await page.evaluate(() => window.scrollY);
  expect(before).toBeGreaterThan(1000);
  const burger = await page.getByRole("button", { name: "Open menu", exact: true }).boundingBox();
  await page.mouse.click(burger!.x + burger!.width / 2, burger!.y + burger!.height / 2);
  const panel = page.getByRole("dialog", { name: "Menu", exact: true });
  await expect(panel).toBeVisible();
  await expect(page.locator(".navbar")).toBeInViewport();
  expect((await page.locator(".navbar").boundingBox())!.y).toBe(0);
  expect(await page.evaluate(() => window.scrollY)).toBe(before);
  await page.mouse.wheel(0, 400);
  expect(await page.evaluate(() => window.scrollY)).toBe(before);
  await panel.getByRole("button", { name: "Close menu", exact: true }).click();
  await expect(panel).toBeHidden();
  await expect(page.locator("#mobile-menu")).toHaveCSS("visibility", "hidden");
  expect(await page.evaluate(() => window.scrollY)).toBe(before);
  await page.mouse.move(150, 400);
  await page.mouse.wheel(0, -200);
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBeLessThan(before);
});

test("every earlier-work card opens its project page", async ({ page }) => {
  await page.goto("/");

  const cards = page.locator(".earlier-grid a.card");
  await expect(cards).toHaveCount(5);

  await page.locator('.earlier-grid a.card[href="/projects/ypsat"]').click();
  await expect(page).toHaveURL(/\/projects\/ypsat\/?$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("YPSat");
});

test("research anchors scroll to their section", async ({ page }) => {
  await page.goto("/research");
  await page.locator('.research-index a[href="#phd"]').click();
  await expect(page).toHaveURL(/\/research\/?#phd$/);
  await expect(page.locator("#phd")).toBeInViewport();
});

test("SolarConflux example navigation and figures work in both themes", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "light" });
  await page.goto("/projects/solarconflux");
  await page.getByRole("link", { name: "Worked example", exact: true }).click();
  await expect(page).toHaveURL(/#example$/);
  await expect(page.locator("#example")).toBeInViewport();
  const lightFigure = page.locator(".solar-chart-light").first();
  const darkFigure = page.locator(".solar-chart-dark").first();
  await expect(lightFigure).toBeVisible();
  await expect(darkFigure).toBeHidden();
  const figureResponse = await page.request.get((await lightFigure.getAttribute("href"))!);
  expect(figureResponse.ok()).toBeTruthy();
  expect(await figureResponse.text()).toContain("<svg");
  const sampleResponse = await page.request.get("/files/solarconflux/january-2025-samples.csv");
  expect(sampleResponse.ok()).toBeTruthy();
  expect((await sampleResponse.text()).trim().split(/\r?\n/)).toHaveLength(58);
  await page.getByRole("button", { name: "Switch to dark mode", exact: true }).click();
  await expect(lightFigure).toBeHidden();
  await expect(darkFigure).toBeVisible();
  await page.locator(".solar-details summary").click();
  await expect(page.getByRole("heading", { name: "Use the Python package", exact: true })).toBeVisible();
  await page.locator(".project-pager-link--next").click();
  await expect(page).toHaveURL(/\/projects\/lunar-spaceport\/?$/);
});

test("Lunar Spaceport connects its pad concept to the report and original figures", async ({ page }) => {
  await page.goto("/projects/lunar-spaceport");
  await page.getByRole("link", { name: "Landing pad", exact: true }).click();
  await expect(page).toHaveURL(/#pad$/);
  await expect(page.locator("#pad")).toBeInViewport();
  await expect(
    page.getByRole("img", { name: "Simplified plan of the proposed lunar landing pad", exact: true }),
  ).toBeVisible();
  const source = page.getByRole("link", { name: "Pad concepts · pp. 19–21", exact: true });
  await expect(source).toHaveAttribute("href", "/files/isureport.pdf#page=36");
  const report = await page.request.get("/files/isureport.pdf");
  expect(report.ok()).toBeTruthy();
  expect((await report.body()).subarray(0, 5).toString()).toBe("%PDF-");
  await page.locator(".spaceport-details summary").click();
  await expect(
    page.getByRole("heading", { name: "Assumptions, not certified requirements", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Original pad rendering · Fig. 1.9", exact: true }),
  ).toBeVisible();
  await page.locator(".project-pager-link--next").click();
  await expect(page).toHaveURL(/\/projects\/ypsat\/?$/);
});

test("Phobos spectroscopy links its redrawn figures to their approximate data and original source", async ({
  page,
}) => {
  await page.goto("/projects/phobos-deimos");

  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Phobos & Deimos");
  await page.getByRole("link", { name: "Through MMX's eyes", exact: true }).click();
  await expect(page).toHaveURL(/#instruments$/);
  await expect(page.locator("#instruments")).toBeInViewport();
  await expect(
    page.getByRole("img", { name: "Seven OROCHI bands used in the study", exact: true }),
  ).toBeVisible();
  const redrawn = page.locator(".phobos-chart--light").first();
  const figure = await page.request.get((await redrawn.getAttribute("href"))!);
  expect(figure.ok()).toBeTruthy();
  expect(figure.headers()["content-type"]).toContain("image/svg+xml");
  expect(await figure.text()).toContain("Approximate digitisation");
  const data = await page.request.get("/files/phobos-deimos/orochi-digitised.csv");
  const rows = (await data.text())
    .trim()
    .split(/\r?\n/)
    .slice(1)
    .map((row) => row.split(","));
  expect(new Set(rows.map((row) => row[2])).size).toBe(8);
  expect(rows.every((row) => Number.isFinite(Number(row[4])))).toBeTruthy();
  expect(rows.filter((row) => row[2].startsWith("CRISM") && Number(row[3]) === 0.65)).toHaveLength(0);
  const source = await page.request.get("/images/projects/phobos-deimos/orochi-report-full.jpg");
  expect(source.ok()).toBeTruthy();
  expect(source.headers()["content-type"]).toContain("image/jpeg");

  const details = page.locator(".project-details");
  await expect(details).not.toHaveAttribute("open", "");
  await details.locator("summary").click();
  await expect(details).toHaveAttribute("open", "");
  await expect(
    page.getByRole("table", { name: "Values used in the 2023 study · Table 4", exact: true }),
  ).toBeVisible();

  await page.locator(".project-pager-link--next").click();
  await expect(page).toHaveURL(/\/projects\/ceres\/?$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Diplona");
});

test("Phobos redrawn spectra stay readable on mobile and switch with the theme", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "light" });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/projects/phobos-deimos#instruments");
  const panels = page.locator(".phobos-spectrum-panel");
  await expect(panels).toHaveCount(4);
  // Measure both panels in one snapshot so lazy images loading above cannot shift them in between.
  const [first, second] = await panels.evaluateAll((els) =>
    els.slice(0, 2).map((el) => el.getBoundingClientRect().toJSON()),
  );
  expect(second.y).toBeGreaterThanOrEqual(first.y + first.height);
  const light = page.locator(".phobos-chart--light").first();
  const dark = page.locator(".phobos-chart--dark").first();
  await expect(light).toBeVisible();
  await expect(dark).toBeHidden();
  await light.scrollIntoViewIfNeeded();
  await expect
    .poll(() => light.locator("img").evaluate((img: HTMLImageElement) => img.currentSrc))
    .toContain("-mobile.svg");
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  await page.getByRole("button", { name: "Switch to dark mode", exact: true }).click();
  await expect(light).toBeHidden();
  await expect(dark).toBeVisible();
  for (const instrument of ["orochi", "mirs"]) {
    const image = page.locator(`.phobos-spectrum--${instrument} .phobos-chart--dark img`).first();
    await image.scrollIntoViewIfNeeded();
    await expect
      .poll(() => image.evaluate((img: HTMLImageElement) => img.complete && img.naturalWidth > 0))
      .toBeTruthy();
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
});

test("Diplona connects its sounding concept and redrawn trade-off to the team report", async ({ page }) => {
  await page.goto("/projects/ceres");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Diplona");
  await page.getByRole("link", { name: "Below the surface", exact: true }).click();
  await expect(page).toHaveURL(/#sounder$/);
  await expect(page.locator("#sounder")).toBeInViewport();
  await expect(
    page.getByRole("img", {
      name: "How the proposed Diplona radar sounder would probe the subsurface",
      exact: true,
    }),
  ).toBeVisible();
  const report = await page.request.get("/files/cerereport.pdf");
  expect(report.ok()).toBeTruthy();
  expect((await report.body()).subarray(0, 5).toString()).toBe("%PDF-");
  const data = await page.request.get("/files/diplona/snr-digitised.csv");
  expect(data.ok()).toBeTruthy();
  const rows = (await data.text())
    .trim()
    .split(/\r?\n/)
    .slice(1)
    .map((row) => row.split(","));
  expect(new Set(rows.map((row) => row[0]))).toEqual(new Set(["24", "28", "32"]));
  expect(rows.every((row) => Number.isFinite(Number(row[2])))).toBeTruthy();
  const source = await page.request.get("/images/projects/ceres/snr-report-original.jpg");
  expect(source.ok()).toBeTruthy();
  await page.locator(".diplona-details summary").click();
  await expect(
    page.getByRole("heading", { name: "Figure source & digitisation", exact: true }),
  ).toBeVisible();
  await page.locator(".project-pager-link--next").click();
  await expect(page).toHaveURL(/\/projects\/solarconflux\/?$/);
});

test("Diplona's figure adapts to mobile, dark mode and narrow screens", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "light" });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/projects/ceres#tradeoffs");
  const light = page.locator(".diplona-chart-light");
  const dark = page.locator(".diplona-chart-dark");
  await light.scrollIntoViewIfNeeded();
  await expect(light).toBeVisible();
  await expect(dark).toBeHidden();
  await expect
    .poll(() => light.locator("img").evaluate((img: HTMLImageElement) => img.currentSrc))
    .toContain("light-mobile.svg");
  await page.getByRole("button", { name: "Switch to dark mode", exact: true }).click();
  await expect(light).toBeHidden();
  await expect(dark).toBeVisible();
  await dark.scrollIntoViewIfNeeded();
  await expect
    .poll(() => dark.locator("img").evaluate((img: HTMLImageElement) => img.currentSrc))
    .toContain("dark-mobile.svg");
  const svg = await page.request.get((await dark.getAttribute("href"))!);
  expect(svg.ok()).toBeTruthy();
  expect(await svg.text()).toContain("Approximate digitisation");
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  await page.setViewportSize({ width: 320, height: 740 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(320);
});

test("YPSat links its wake-up sequence, flight image and source notes", async ({ page }) => {
  await page.goto("/projects/ypsat");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("YPSat");
  await expect(page.locator(".ypsat-hero-art")).toHaveAttribute(
    "src",
    "/images/projects/ypsat/ariane-six-launch.webp",
  );
  const flightLink = page.getByRole("link", { name: "See the flight results", exact: true });
  await expect(flightLink).toHaveAttribute(
    "href",
    "https://www.esa.int/Enabling_Support/Space_Transportation/Ariane/Ariane_6_post-launch_update",
  );
  await expect(flightLink.locator("img")).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Discuss the project", exact: true })).toHaveCount(0);
  await expect(
    page.getByText("Simplified logic from ESA's public system description.", { exact: true }),
  ).toHaveCount(0);
  await page.getByRole("link", { name: "Waking up", exact: true }).click();
  await expect(page).toHaveURL(/#wakeup$/);
  await expect(page.locator("#wakeup")).toBeInViewport();
  const steps = page.getByRole("list", { name: "Simplified YPSat wake-up sequence", exact: true });
  await expect(steps.locator("li")).toHaveCount(4);
  await expect(page.locator(".ypsat-backup")).toContainText("deployment signal");
  await expect(page.getByRole("link", { name: "ESA · wake-up subsystem", exact: true })).toHaveAttribute(
    "href",
    "https://www.esa.int/ESA_Multimedia/Images/2024/06/Wake-up_subsystem",
  );
  const image = await page.request.get("/images/earth.webp");
  expect(image.ok()).toBeTruthy();
  expect(image.headers()["content-type"]).toContain("image/webp");
  await page.locator(".ypsat-details summary").click();
  await expect(page.getByRole("heading", { name: "Reading the sequence", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Image source & licence", exact: true })).toHaveAttribute(
    "href",
    "https://www.esa.int/ESA_Multimedia/Images/2024/07/YPSat_looks_back_to_Earth_from_atop_Ariane_6",
  );
  await page.locator(".project-pager-link--next").click();
  await expect(page).toHaveURL(/\/projects\/phobos-deimos\/?$/);
});

test("Project contact actions and the shared email link use the envelope illustration", async ({ page }) => {
  for (const project of ["ypsat", "lunar-spaceport", "phobos-deimos", "ceres"]) {
    await page.goto(`/projects/${project}`);
    const contact = page.getByRole("link", { name: "Ask me about it", exact: true });
    await expect(contact).toHaveAttribute("href", "/#contact");
    await expect(contact.locator("img")).toHaveAttribute("src", "/images/accents/contact.webp");
    await expect
      .poll(() =>
        contact
          .locator("img")
          .evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth > 0),
      )
      .toBeTruthy();
    await expect(page.locator(".site-footer-email img")).toHaveAttribute(
      "src",
      "/images/accents/contact.webp",
    );
  }
});

test("YPSat's sequence and transparent artwork adapt to mobile and dark mode", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "light" });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/projects/ypsat");
  const hero = page.locator(".ypsat-hero-art");
  await hero.scrollIntoViewIfNeeded();
  await expect
    .poll(() => hero.evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth > 0))
    .toBeTruthy();
  const artwork = await page.request.get((await hero.getAttribute("src"))!);
  expect(artwork.ok()).toBeTruthy();
  await page.getByRole("link", { name: "Waking up", exact: true }).click();
  // Measure both steps in one frame: the anchor click starts a smooth scroll.
  const [first, second] = await page
    .locator(".ypsat-sequence li")
    .evaluateAll((items) => items.slice(0, 2).map((item) => item.getBoundingClientRect().toJSON()));
  expect(second.y).toBeGreaterThanOrEqual(first.y + first.height - 1);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(390);
  await page.getByRole("button", { name: "Switch to dark mode", exact: true }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  const board = page.locator(".ypsat-board-figure img");
  await board.scrollIntoViewIfNeeded();
  await expect
    .poll(() => board.evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth > 0))
    .toBeTruthy();
  await page.setViewportSize({ width: 320, height: 740 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(320);
});
