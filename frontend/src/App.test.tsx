import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import App from "./App";
import { info, json } from "./test/fixtures";
function healthy() {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) =>
      Promise.resolve(
        json(
          url.endsWith("/health") ? { status: "ok", model_ready: true } : info,
        ),
      ),
    ),
  );
}
async function navigate(id: string) {
  await act(async () => {
    window.location.hash = id;
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  });
}
describe("dashboard navigation and truthful status", () => {
  it("shows documented historical figures and no live shipment KPIs", async () => {
    healthy();
    render(<App />);
    expect(await screen.findByText("API connected")).toBeInTheDocument();
    expect(screen.getByText("0.7494")).toBeInTheDocument();
    expect(
      screen.getByText(/No live shipments are connected/),
    ).toBeInTheDocument();
    expect(screen.getByText(/every test order late/)).toBeInTheDocument();
    await navigate("insights");
    expect(
      screen.getByRole("heading", { level: 1, name: "Model Insights" }),
    ).toBeInTheDocument();
    expect(screen.getByText("5,547")).toBeInTheDocument();
    expect(
      screen.getByText("Days for shipment (scheduled)"),
    ).toBeInTheDocument();
    await navigate("about");
    expect(screen.getByRole("link", { name: /API reference/ })).toHaveAttribute(
      "href",
      "/docs/API.md",
    );
  });
  it("distinguishes a disconnected backend from an unavailable model and can retry", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    window.location.hash = "status";
    render(<App />);
    expect(
      await screen.findByRole("heading", { name: "Backend unavailable" }),
    ).toBeInTheDocument();
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          json(
            url.endsWith("/health")
              ? { status: "ok", model_ready: false }
              : {
                  ...info,
                  model_ready: false,
                  readiness_status: "unavailable",
                  unavailable_reason: "trust_not_enabled",
                  allowed_categories: {},
                },
          ),
        ),
      ),
    );
    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: /Refresh status/ }));
    expect(
      await screen.findByRole("heading", {
        name: "Backend connected · model not ready",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/trust not enabled/)).toBeInTheDocument();
  });
  it("supports the mobile navigation toggle and unknown page recovery", async () => {
    healthy();
    render(<App />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Open navigation" }));
    expect(
      screen.getByRole("button", { name: "Close navigation" }),
    ).toHaveAttribute("aria-expanded", "true");
    await navigate("prediction");
    expect(
      screen.getByRole("button", { name: "Open navigation" }),
    ).toHaveAttribute("aria-expanded", "false");
    await navigate("missing");
    await waitFor(() =>
      expect(
        screen.getByRole("heading", { name: "Page not found" }),
      ).toBeInTheDocument(),
    );
  });
});
