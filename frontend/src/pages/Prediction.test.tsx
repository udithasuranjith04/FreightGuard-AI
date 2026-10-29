import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Prediction } from "./Prediction";
import { info, json, payload, prediction } from "../test/fixtures";

async function fill() {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText(/Scheduled shipping days/), "4");
  for (const [label, value] of [
    ["Shipping mode", "Standard Class"],
    ["Market", "Europe"],
    ["Order region", "Western Europe"],
    ["Order country", "Francia"],
  ]) {
    await user.selectOptions(screen.getByLabelText(new RegExp(label!)), value!);
  }
  return user;
}
describe("shipment prediction form", () => {
  it("uses exactly five accessible inputs and prevents invalid submission", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    render(<Prediction info={info} loading={false} />);
    expect(screen.getAllByRole("combobox")).toHaveLength(4);
    const user = userEvent.setup();
    await user.click(
      screen.getByRole("button", { name: /Calculate experimental risk/ }),
    );
    expect(
      screen.getByText("Enter a whole number from 0 to 4."),
    ).toBeInTheDocument();
    expect(screen.getByRole("spinbutton")).toHaveFocus();
    expect(fetchMock).not.toHaveBeenCalled();
  });
  it("handles loading, sends the contract and displays the honest result", async () => {
    let resolve!: (response: Response) => void;
    const fetchMock = vi.fn().mockReturnValue(
      new Promise<Response>((done) => {
        resolve = done;
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    render(<Prediction info={info} loading={false} />);
    const user = await fill();
    await user.click(
      screen.getByRole("button", { name: /Calculate experimental risk/ }),
    );
    expect(screen.getByRole("button", { name: /Calculating/ })).toBeDisabled();
    expect(
      JSON.parse(
        (fetchMock.mock.calls[0] as [string, RequestInit])[1].body as string,
      ),
    ).toEqual(payload);
    resolve(json(prediction));
    expect(await screen.findByText("42.7")).toBeInTheDocument();
    expect(screen.getByText("Late", { exact: true })).toBeInTheDocument();
    expect(screen.getByText(/not a delivery guarantee/)).toBeInTheDocument();
    await user.selectOptions(
      screen.getByLabelText(/Shipping mode/),
      "Same Day",
    );
    expect(screen.queryByText("42.7")).not.toBeInTheDocument();
  });
  it.each([503, 422, 500])(
    "allows recovery from API error %s",
    async (status) => {
      const code =
        status === 503
          ? "model_unavailable"
          : status === 422
            ? "validation_error"
            : "internal_error";
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue(
          json(
            {
              error: {
                code,
                fields: status === 422 ? ["order_country"] : [],
              },
            },
            status,
          ),
        ),
      );
      render(<Prediction info={info} loading={false} />);
      const user = await fill();
      await user.click(
        screen.getByRole("button", { name: /Calculate experimental risk/ }),
      );
      expect(await screen.findByRole("alert")).toBeInTheDocument();
      expect(screen.queryByText("42.7")).not.toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /Calculate experimental risk/ }),
      ).toBeEnabled();
      await user.click(screen.getByRole("button", { name: "Reset" }));
      expect(screen.getByRole("spinbutton")).toHaveValue(null);
      expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    },
  );
  it("disables submission when the model is unavailable", () => {
    render(
      <Prediction info={{ ...info, model_ready: false }} loading={false} />,
    );
    expect(
      screen.getByRole("button", { name: /Calculate experimental risk/ }),
    ).toBeDisabled();
    expect(screen.getByText(/Predictions are unavailable/)).toBeInTheDocument();
  });
  it("rejects fractional and out of range days client-side", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    render(<Prediction info={info} loading={false} />);
    const user = await fill();
    fireEvent.change(screen.getByRole("spinbutton"), {
      target: { value: "4.5" },
    });
    await user.click(
      screen.getByRole("button", { name: /Calculate experimental risk/ }),
    );
    await waitFor(() =>
      expect(screen.getByRole("spinbutton")).toHaveAttribute(
        "aria-invalid",
        "true",
      ),
    );
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

it("displays a not-late response without changing the model label", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      json({
        ...prediction,
        risk_score: 0.2,
        experimental_prediction: "not_late",
      }),
    ),
  );
  render(<Prediction info={info} loading={false} />);
  const user = await fill();
  await user.click(
    screen.getByRole("button", { name: /Calculate experimental risk/ }),
  );
  expect(
    await screen.findByText("Not late", { exact: true }),
  ).toBeInTheDocument();
  expect(screen.getByText("20.0")).toBeInTheDocument();
  expect(screen.getByText(/not a delivery guarantee/)).toBeInTheDocument();
});
