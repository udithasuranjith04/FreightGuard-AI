import { describe, expect, it, vi } from "vitest";
import { api, ApiError, infoSchema, requestSchema, validateInput } from "./api";
import { info, json, payload, prediction } from "./test/fixtures";

describe("five-input contract", () => {
  it("accepts only the exact approved input", () => {
    expect(validateInput(payload, info)).toEqual({});
    expect(
      requestSchema.safeParse({
        ...payload,
        email: "synthetic@example.invalid",
      }).success,
    ).toBe(false);
    expect(
      requestSchema.safeParse({ ...payload, delivery_status: "Late" }).success,
    ).toBe(false);
  });
  it.each([-1, 5, 1.5, "4", true, null, NaN, Infinity])(
    "rejects invalid scheduled days %s",
    (value) => {
      expect(
        validateInput({ ...payload, scheduled_shipping_days: value }, info)
          .scheduled_shipping_days,
      ).toBeTruthy();
    },
  );
  it.each(["shipping_mode", "market", "order_country", "order_region"])(
    "rejects unknown categories in %s",
    (field) => {
      expect(
        validateInput({ ...payload, [field]: "Unsupported" }, info)[
          field as keyof typeof payload
        ],
      ).toBeTruthy();
    },
  );
  it("rejects missing inputs and sensitive text", () => {
    expect(Object.keys(validateInput({}, info))).toHaveLength(5);
    expect(
      validateInput(
        { ...payload, order_country: "contact@example.invalid" },
        info,
      ).order_country,
    ).toBeTruthy();
  });
  it("rejects a changed threshold or operational validation contract", () => {
    expect(infoSchema.safeParse({ ...info, threshold: 0.5 }).success).toBe(
      false,
    );
    expect(
      infoSchema.safeParse({ ...info, operationally_validated: true }).success,
    ).toBe(false);
  });
});
describe("typed API client", () => {
  it("posts exactly five fields with no credentials", async () => {
    const fetchMock = vi.fn().mockResolvedValue(json(prediction));
    vi.stubGlobal("fetch", fetchMock);
    expect(await api.predict(payload)).toEqual(prediction);
    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(JSON.parse(options.body as string)).toEqual(payload);
    expect(options.credentials).toBe("omit");
    expect(options.method).toBe("POST");
  });
  it("handles network failure without exposing details", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("/private/secret")),
    );
    await expect(api.health()).rejects.toMatchObject({ code: "connection" });
  });
  it("handles malformed JSON and incompatible success responses", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("invalid")));
    await expect(api.info()).rejects.toMatchObject({ code: "response" });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(json({ late_probability: 0.5 })),
    );
    await expect(api.predict(payload)).rejects.toMatchObject({
      code: "response",
    });
  });
  it("maps unavailable and validation errors without trusting server messages", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        json(
          {
            error: {
              code: "model_unavailable",
              message: "/private/path",
              fields: [],
            },
          },
          503,
        ),
      ),
    );
    await expect(api.predict(payload)).rejects.toMatchObject({
      code: "model_unavailable",
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        json(
          {
            error: {
              code: "validation_error",
              message: "private value",
              fields: ["order_country", "secret"],
            },
          },
          422,
        ),
      ),
    );
    try {
      await api.predict(payload);
      expect.fail("must fail");
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).fields).toEqual(["order_country"]);
      expect((error as ApiError).message).not.toContain("private");
    }
  });
});
