import type { ModelInfo, Prediction } from "../api";
export const info: ModelInfo = {
  model_version: "v1",
  model_ready: true,
  readiness_status: "ready_for_educational_demo",
  unavailable_reason: null,
  operationally_validated: false,
  threshold: 0.4,
  approved_features: [
    "Days for shipment (scheduled)",
    "Shipping Mode",
    "Market",
    "Order Region",
    "Order Country",
  ],
  request_fields: [
    "scheduled_shipping_days",
    "shipping_mode",
    "market",
    "order_region",
    "order_country",
  ],
  limitations: [
    "Educational model: primarily shipping-plan patterns, not validated order-specific operational alerts.",
  ],
  allowed_categories: {
    shipping_mode: ["Standard Class", "Same Day"],
    market: ["Europe"],
    order_region: ["Western Europe"],
    order_country: ["Francia"],
  },
};
export const payload = {
  scheduled_shipping_days: 4,
  shipping_mode: "Standard Class",
  market: "Europe",
  order_region: "Western Europe",
  order_country: "Francia",
} as const;
export const prediction: Prediction = {
  risk_score: 0.4272314668675644,
  experimental_prediction: "late",
  model_version: "v1",
  threshold: 0.4,
  experimental: true,
  operationally_validated: false,
  warnings: info.limitations,
};
export const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
