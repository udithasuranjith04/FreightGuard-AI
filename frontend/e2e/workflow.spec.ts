import { expect, test } from "@playwright/test";
// Requires the two local servers. No mocks: only an invented five-input shipment.
test("synthetic shipment through the browser and frozen local API", async ({
  page,
}, testInfo) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(page.getByText("API connected", { exact: true })).toBeVisible();
  await expect(page.getByText("0.7494", { exact: true })).toBeVisible();
  if (testInfo.project.name === "mobile")
    await page.getByRole("button", { name: "Open navigation" }).click();
  await page
    .getByRole("link", { name: "Shipment Prediction", exact: true })
    .click();
  await page.getByLabel("Scheduled shipping days").fill("4");
  await page
    .getByRole("combobox", { name: "Shipping mode", exact: true })
    .selectOption("Standard Class");
  await page
    .getByRole("combobox", { name: "Market", exact: true })
    .selectOption("Europe");
  await page
    .getByRole("combobox", { name: "Order region", exact: true })
    .selectOption("Western Europe");
  await page
    .getByRole("combobox", { name: "Order country", exact: true })
    .selectOption("Francia");
  const request = page.waitForRequest(
    (req) => req.url().endsWith("/predict") && req.method() === "POST",
  );
  await page
    .getByRole("button", { name: "Calculate experimental risk" })
    .click();
  expect(Object.keys((await request).postDataJSON()).sort()).toEqual([
    "market",
    "order_country",
    "order_region",
    "scheduled_shipping_days",
    "shipping_mode",
  ]);
  await expect(page.getByText("42.7%", { exact: true })).toBeVisible();
  await expect(page.getByText("Late", { exact: true })).toBeVisible();
  await expect(
    page.getByText(
      "Model v1 · Fixed threshold 0.40 · Operationally validated: No",
    ),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: testInfo.outputPath("prediction.png"),
    fullPage: true,
  });
  if (testInfo.project.name === "mobile")
    await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("link", { name: "System Status", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Ready for educational inference" }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

test("all pages, keyboard skip link, documentation and responsive layout", async ({
  page,
}, testInfo) => {
  await page.goto("/");
  await expect(page.getByText("API connected", { exact: true })).toBeVisible();
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("link", { name: "Skip to content" }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("main")).toBeFocused();
  await page.screenshot({
    path: testInfo.outputPath("overview.png"),
    fullPage: true,
  });
  for (const [name, title] of [
    ["Model Insights", "Model Insights"],
    ["About & Documentation", "About FreightGuard AI"],
  ]) {
    if (testInfo.project.name === "mobile")
      await page.getByRole("button", { name: "Open navigation" }).click();
    await page.getByRole("link", { name, exact: true }).click();
    await expect(
      page.getByRole("heading", { level: 1, name: title }),
    ).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
    await page.screenshot({
      path: testInfo.outputPath(`${title}.png`),
      fullPage: true,
    });
  }
  for (const name of [
    "API.md",
    "TRAINING.md",
    "MODEL_QUALITY.md",
    "ARCHITECTURE.md",
    "FRONTEND.md",
  ]) {
    const response = await page.request.get(`/docs/${name}`);
    expect(response.status()).toBe(200);
    expect(response.headers()["content-type"]).toMatch(/^text\/(plain|markdown)/);
    expect(await response.text()).toMatch(/^# /);
  }
});

test("offline backend and unavailable model are distinct browser states", async ({
  page,
}) => {
  await page.route("**/health", (route) => route.abort());
  await page.route("**/model/info", (route) => route.abort());
  await page.goto("/#status");
  await expect(
    page.getByRole("heading", { name: "Backend unavailable" }),
  ).toBeVisible();
  // Fault injection only; historical dashboard figures are never mock operational data.
  await page.route("**/health", (route) =>
    route.fulfill({ json: { status: "ok", model_ready: false } }),
  );
  await page.unroute("**/model/info");
  await page.route("**/model/info", async (route) => {
    const response = await route.fetch();
    const info = await response.json();
    await route.fulfill({
      json: {
        ...info,
        model_ready: false,
        readiness_status: "unavailable",
        unavailable_reason: "artifact_missing",
        allowed_categories: {},
      },
    });
  });
  await page.getByRole("button", { name: "Refresh status" }).click();
  await expect(
    page.getByRole("heading", { name: "Backend connected · model not ready" }),
  ).toBeVisible();
  await page.goto("/#prediction");
  await expect(
    page.getByRole("button", { name: "Calculate experimental risk" }),
  ).toBeDisabled();
  await expect(page.getByText(/Predictions are unavailable/)).toBeVisible();
});
