import { z } from "zod";

export const fields = [
  "scheduled_shipping_days",
  "shipping_mode",
  "market",
  "order_region",
  "order_country",
] as const;
export type FieldName = (typeof fields)[number];
export const labels: Record<FieldName, string> = {
  scheduled_shipping_days: "Scheduled shipping days",
  shipping_mode: "Shipping mode",
  market: "Market",
  order_region: "Order region",
  order_country: "Order country",
};
const geography = z
  .string()
  .min(2)
  .max(80)
  .refine((v) => /\p{L}/u.test(v) && /^[\p{L}\p{M} .\-'’()]+$/u.test(v));
export const requestSchema = z
  .object({
    scheduled_shipping_days: z.number().int().min(0).max(4),
    shipping_mode: z.enum([
      "Standard Class",
      "First Class",
      "Second Class",
      "Same Day",
    ]),
    market: z.enum(["Africa", "Europe", "LATAM", "Pacific Asia", "USCA"]),
    order_region: geography,
    order_country: geography,
  })
  .strict();
export type PredictionInput = z.infer<typeof requestSchema>;
export const healthSchema = z.object({
  status: z.literal("ok"),
  model_ready: z.boolean(),
});
export const infoSchema = z.object({
  model_version: z.literal("v1"),
  model_ready: z.boolean(),
  readiness_status: z.enum(["ready_for_educational_demo", "unavailable"]),
  unavailable_reason: z.string().nullable(),
  operationally_validated: z.literal(false),
  threshold: z.literal(0.4),
  approved_features: z.array(z.string()),
  request_fields: z.array(z.string()),
  limitations: z.array(z.string()),
  allowed_categories: z.record(z.string(), z.array(z.string())),
});
export const predictionSchema = z.object({
  risk_score: z.number().min(0).max(1),
  experimental_prediction: z.enum(["late", "not_late"]),
  model_version: z.literal("v1"),
  threshold: z.literal(0.4),
  experimental: z.literal(true),
  operationally_validated: z.literal(false),
  warnings: z.array(z.string()),
});
export type Health = z.infer<typeof healthSchema>;
export type ModelInfo = z.infer<typeof infoSchema>;
export type Prediction = z.infer<typeof predictionSchema>;
export const API_BASE = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");
const configuredUrl = new URL(API_BASE);
if (
  !["http:", "https:"].includes(configuredUrl.protocol) ||
  configuredUrl.username ||
  configuredUrl.password ||
  configuredUrl.search ||
  configuredUrl.hash
) {
  throw new Error(
    "VITE_API_BASE_URL requires an HTTP(S) URL without credentials, query or fragment.",
  );
}
export class ApiError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly fields: string[] = [],
  ) {
    super(message);
  }
}
const safeErrors: Record<string, string> = {
  validation_error: "Check the five inputs and select supported categories.",
  model_unavailable:
    "The backend is reachable, but the educational model is unavailable. Check System Status.",
  internal_error:
    "Prediction could not be completed. Try again or check System Status.",
  payload_too_large: "The request is too large.",
  unsupported_media_type: "The API requires a JSON request.",
};
async function request<T>(
  path: string,
  schema: z.ZodType<T>,
  input?: PredictionInput,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: input ? "POST" : "GET",
      headers: input ? { "Content-Type": "application/json" } : undefined,
      body: input ? JSON.stringify(input) : undefined,
      signal: AbortSignal.timeout(12000),
      credentials: "omit",
    });
  } catch {
    throw new ApiError(
      "connection",
      "Cannot reach the backend. Check that it is running and the API URL and CORS origins are configured.",
    );
  }
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw new ApiError("response", "The API returned an unexpected response.");
  }
  if (!response.ok) {
    const error = z
      .object({
        error: z.object({ code: z.string(), fields: z.array(z.string()) }),
      })
      .safeParse(body);
    const code = error.success ? error.data.error.code : "response";
    throw new ApiError(
      code,
      safeErrors[code] ||
        "The API request failed. Check System Status and try again.",
      error.success
        ? error.data.error.fields.filter((f) => fields.includes(f as FieldName))
        : [],
    );
  }
  const result = schema.safeParse(body);
  if (!result.success)
    throw new ApiError(
      "response",
      "The API response does not match the supported v1 contract.",
    );
  return result.data;
}
export const api = {
  health: () => request("/health", healthSchema),
  info: () => request("/model/info", infoSchema),
  predict: (input: PredictionInput) =>
    request("/predict", predictionSchema, requestSchema.parse(input)),
};
export function validateInput(
  value: unknown,
  info: ModelInfo,
): Partial<Record<FieldName, string>> {
  const parsed = requestSchema.safeParse(value);
  const errors: Partial<Record<FieldName, string>> = {};
  if (!parsed.success) {
    for (const issue of parsed.error.issues) {
      const field = issue.path[0] as FieldName;
      if (fields.includes(field))
        errors[field] =
          field === "scheduled_shipping_days"
            ? "Enter a whole number from 0 to 4."
            : "Select a supported value.";
    }
    return errors;
  }
  for (const field of fields.slice(1)) {
    if (!info.allowed_categories[field]?.includes(String(parsed.data[field])))
      errors[field] = "Select a supported category from the model.";
  }
  return errors;
}
