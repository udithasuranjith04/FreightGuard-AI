// Manually transcribed public aggregates from docs/TRAINING.md, Results (2026-10-28).
// This is a historical snapshot, never live telemetry; no artifact/data fetch occurs.
export const evaluation = {
  date: "28 Oct 2026",
  testOrders: 13071,
  validationOrders: 9497,
  metrics: [
    { label: "ROC-AUC", value: "0.7494", detail: "Global score ranking" },
    {
      label: "Precision",
      value: "57.56%",
      detail: "Late among predicted late",
    },
    { label: "Recall", value: "100%", detail: "All orders predicted late" },
    { label: "F1 score", value: "0.7307", detail: "Frozen threshold · 0.40" },
  ],
  candidates: [
    {
      name: "Always-late baseline",
      threshold: "0.50",
      precision: "0.5660",
      recall: "1.0000",
      f1: "0.7228",
      auc: "0.5000",
    },
    {
      name: "Logistic Regression",
      threshold: "0.30",
      precision: "0.5669",
      recall: "0.9981",
      f1: "0.7231",
      auc: "0.7398",
    },
    {
      name: "Random Forest",
      threshold: "0.40",
      precision: "0.5753",
      recall: "0.9790",
      f1: "0.7247",
      auc: "0.7426",
    },
  ],
  confusion: [
    { label: "True negatives", value: 0 },
    { label: "False positives", value: 5547 },
    { label: "False negatives", value: 0 },
    { label: "True positives", value: 7524 },
  ],
  importance: [
    { label: "Shipping mode", value: 68.78 },
    { label: "Scheduled days", value: 29.59 },
    { label: "Broad geography", value: 1.63 },
  ],
} as const;
