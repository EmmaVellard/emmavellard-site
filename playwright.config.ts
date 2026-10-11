import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: "http://127.0.0.1:4322",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    // --ignore-lock keeps the server in the foreground: Astro otherwise backgrounds it when an
    // AI coding agent is detected, and Playwright then sees the process exit early.
    command: "npm run preview -- --host 127.0.0.1 --port 4322 --ignore-lock",
    url: "http://127.0.0.1:4322",
    reuseExistingServer: !process.env.CI,
  },
});
