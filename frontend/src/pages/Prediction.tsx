import { useRef, useState } from "react";
import type { FormEvent } from "react";
import { ArrowRight, Box, RotateCcw, ShieldCheck } from "lucide-react";
import { api, ApiError, fields, labels, validateInput } from "../api";
import type {
  FieldName,
  ModelInfo,
  Prediction as PredictionResult,
  PredictionInput,
} from "../api";
import { Badge, Button, Card, Notice } from "../components/ui";

const empty = {
  scheduled_shipping_days: "",
  shipping_mode: "",
  market: "",
  order_region: "",
  order_country: "",
};
type Draft = Record<FieldName, string>;
export function Prediction({
  info,
  loading,
}: {
  info: ModelInfo | null;
  loading: boolean;
}) {
  const [draft, setDraft] = useState<Draft>(empty);
  const [errors, setErrors] = useState<Partial<Record<FieldName, string>>>({});
  const [pending, setPending] = useState(false);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const resultRef = useRef<HTMLDivElement>(null);
  const ready = info?.model_ready === true;
  function change(field: FieldName, value: string) {
    setDraft((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
    setResult(null);
    setFailure(null);
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!info || !ready || pending) return;
    const input = {
      ...draft,
      scheduled_shipping_days:
        draft.scheduled_shipping_days === ""
          ? NaN
          : Number(draft.scheduled_shipping_days),
    };
    const issues = validateInput(input, info);
    setErrors(issues);
    setResult(null);
    setFailure(null);
    const first = fields.find((field) => issues[field]);
    if (first) {
      document.getElementById(first)?.focus();
      return;
    }
    setPending(true);
    try {
      const response = await api.predict(input as PredictionInput);
      setResult(response);
      window.setTimeout(() => resultRef.current?.focus(), 0);
    } catch (error) {
      setFailure(
        error instanceof ApiError
          ? error.message
          : "Prediction failed. Please try again.",
      );
      if (error instanceof ApiError)
        setErrors(
          Object.fromEntries(
            error.fields.map((field) => [
              field,
              "Check this input against supported values.",
            ]),
          ),
        );
    } finally {
      setPending(false);
    }
  }
  function reset() {
    setDraft(empty);
    setResult(null);
    setErrors({});
    setFailure(null);
  }
  return (
    <div className="page-content">
      <Notice />
      <div className="grid items-start gap-6 xl:grid-cols-[1.1fr_1fr]">
        <Card
          title="Shipment details"
          eyebrow="Five approved inputs"
          action={<Box size={21} className="muted" />}
        >
          <p className="muted mb-6 text-sm">
            Use the shipping plan finalized at checkout, before dispatch. Do not
            enter customer information or delivery outcomes.
          </p>
          {!ready && (
            <div role="status" className="subtle-box mb-5">
              {loading
                ? "Checking model availability…"
                : "Predictions are unavailable until the backend and trusted model are ready."}{" "}
              <a className="text-link" href="#status">
                Check System Status <ArrowRight size={14} />
              </a>
            </div>
          )}
          <form
            onSubmit={(event) => {
              void submit(event);
            }}
            noValidate
          >
            <fieldset
              disabled={!ready || pending || loading}
              className="grid gap-5 sm:grid-cols-2"
            >
              <legend className="sr-only">Approved shipment inputs</legend>
              {fields.map((field) => (
                <div
                  className={
                    field === "scheduled_shipping_days" ? "sm:col-span-2" : ""
                  }
                  key={field}
                >
                  <label htmlFor={field}>
                    {labels[field]}{" "}
                    <span className="required" aria-hidden="true">
                      *
                    </span>
                  </label>
                  {field === "scheduled_shipping_days" ? (
                    <>
                      <input
                        id={field}
                        name={field}
                        type="number"
                        min="0"
                        max="4"
                        step="1"
                        required
                        value={draft[field]}
                        onChange={(event) => change(field, event.target.value)}
                        aria-invalid={!!errors[field]}
                        aria-describedby={`${field}-hint ${field}-error`}
                        placeholder="e.g. 4"
                      />
                      <p id={`${field}-hint`} className="field-hint">
                        Whole number from 0 to 4. Scheduled duration, never
                        actual duration.
                      </p>
                    </>
                  ) : (
                    <select
                      id={field}
                      name={field}
                      required
                      value={draft[field]}
                      onChange={(event) => change(field, event.target.value)}
                      aria-invalid={!!errors[field]}
                      aria-describedby={`${field}-error`}
                    >
                      <option value="">
                        Select {labels[field].toLowerCase()}
                      </option>
                      {(info?.allowed_categories[field] ?? []).map((value) => (
                        <option key={value} value={value}>
                          {value}
                        </option>
                      ))}
                    </select>
                  )}
                  <p className="field-error" id={`${field}-error`}>
                    {errors[field]}
                  </p>
                </div>
              ))}
            </fieldset>
            <p className="field-hint mt-2">
              All five fields are required. Geography uses the model’s original
              category spellings. Category combinations are not verified as
              valid routes.
            </p>
            {failure && (
              <div role="alert" className="error-box mt-5">
                {failure}
              </div>
            )}
            <div className="form-actions">
              <Button type="submit" disabled={!ready || loading || pending}>
                {pending ? (
                  <>
                    <span className="spinner" />
                    Calculating…
                  </>
                ) : (
                  <>
                    Calculate experimental risk <ArrowRight size={17} />
                  </>
                )}
              </Button>
              <Button
                type="button"
                secondary
                onClick={reset}
                disabled={pending}
              >
                <RotateCcw size={15} />
                Reset
              </Button>
            </div>
          </form>
        </Card>
        <div className="space-y-5">
          <div
            ref={resultRef}
            tabIndex={-1}
            aria-live="polite"
            aria-atomic="true"
            className="result-container"
          >
            <Card
              title="Experimental result"
              action={<Badge tone="warning">Research only</Badge>}
            >
              {pending ? (
                <div role="status" className="empty-result">
                  <span className="spinner" />
                  <h3>Calculating your model score</h3>
                  <p>Using the unchanged v1 pipeline.</p>
                </div>
              ) : result ? (
                <>
                  <p className="eyebrow mt-5">EXPERIMENTAL DELAY RISK SCORE</p>
                  <p className="risk-value">
                    {(result.risk_score * 100).toFixed(1)}
                    <span>%</span>
                  </p>
                  <div className="risk-track">
                    <div style={{ width: `${result.risk_score * 100}%` }} />
                    <span style={{ left: `${result.threshold * 100}%` }} />
                  </div>
                  <div className="flex justify-between text-xs muted mt-2">
                    <span>0%</span>
                    <span>Frozen cutoff: 40%</span>
                    <span>100%</span>
                  </div>
                  <div className="classification">
                    <span>Frozen model classification</span>
                    <strong>
                      {result.experimental_prediction === "late"
                        ? "Late"
                        : "Not late"}
                    </strong>
                  </div>
                  <p className="muted text-sm mt-4">
                    This is an experimental model score, not a delivery
                    guarantee or validated probability for this shipment. Risk
                    is conditional on eventual non-cancellation.
                  </p>
                  <ul className="warning-list">
                    {result.warnings.map((warning) => (
                      <li key={warning}>{warning}</li>
                    ))}
                  </ul>
                  <p className="source-note">
                    Model {result.model_version} · Fixed threshold{" "}
                    {result.threshold.toFixed(2)} · Operationally validated: No
                  </p>
                </>
              ) : (
                <div className="empty-result">
                  <span className="empty-icon">
                    <ShieldCheck size={34} strokeWidth={1.3} />
                  </span>
                  <h3>Your prediction will appear here</h3>
                  <p>
                    Enter the five approved shipment inputs to explore the
                    frozen educational model.
                  </p>
                  <span className="mini-label">
                    NO SHIPMENT RECORDS ARE STORED
                  </span>
                </div>
              )}
            </Card>
          </div>
          <div className="subtle-box">
            <h3>What this score can tell you</h3>
            <p className="muted text-sm mt-2">
              V1 reflects historical shipping-plan associations. It cannot
              reliably rank orders within the same shipping mode. A “late”
              result is not evidence that an operational intervention is needed.
            </p>
            <a className="text-link mt-3" href="#insights">
              Understand the model <ArrowRight size={14} />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
