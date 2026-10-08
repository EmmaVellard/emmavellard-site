import { expect, test } from "@playwright/test";

test("the homepage uses the brand as its home link and has no footer", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("link", { name: "Emma Vellard" })).toHaveAttribute("href", "/");
  await expect(page.getByRole("link", { name: "Home", exact: true })).toHaveCount(0);
  await expect(page.locator("footer")).toHaveCount(0);
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

test("every available project card is clickable and named by its title", async ({ page }) => {
  await page.goto("/projects");

  const titleLinks = page.locator(".proj-card-link a.proj-card-title-link");
  await expect(titleLinks).toHaveCount(5);
  await expect(page.getByRole("link", { name: "Diplona", exact: true })).toHaveAttribute(
    "href",
    "/projects/ceres",
  );

  // Clicking the card body (not the title) still navigates thanks to the stretched link.
  // Center the card first so the fixed navbar does not cover the click target.
  await page.locator("#ceres").evaluate((card) => card.scrollIntoView({ block: "center" }));
  const box = await page.locator("#ceres .proj-desc").boundingBox();
  expect(box).not.toBeNull();
  await page.mouse.click(box!.x + box!.width / 2, box!.y + box!.height / 2);
  await expect(page).toHaveURL(/\/projects\/ceres\/?$/);
});

test("experience and project section navigation follow anchor links", async ({ page }) => {
  await page.goto("/experience");
  const esaLink = page.locator('[data-section-nav] a[href="#esa"]');
  await esaLink.click();
  await expect(page).toHaveURL(/\/experience\/?#esa$/);
  await expect(esaLink).toHaveAttribute("aria-current", "location");

  await page.goto("/projects/ceres");
  const measurementLink = page.locator('[data-section-nav] a[href="#measurement"]');
  await measurementLink.click();
  await expect(page).toHaveURL(/\/projects\/ceres\/?#measurement$/);
  await expect(measurementLink).toHaveAttribute("aria-current", "location");
});

test("the contact footer fits in a standard viewport without artificial scrolling", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/contact");

  const layout = await page.evaluate(() => ({
    viewportHeight: window.innerHeight,
    documentHeight: document.documentElement.scrollHeight,
    footerBottom: document.querySelector("footer")?.getBoundingClientRect().bottom ?? 0,
  }));

  expect(layout.documentHeight).toBeLessThanOrEqual(layout.viewportHeight + 1);
  expect(layout.footerBottom).toBeLessThanOrEqual(layout.viewportHeight + 1);
});
