import { Card, Badge, DocLink, Notice } from "../components/ui";
import { Importance, Metrics } from "./Overview";
import { evaluation } from "../evaluation";
import type { ModelInfo } from "../api";
export function Insights({
  info,
  error,
  loading,
}: {
  info: ModelInfo | null;
  error: string | null;
  loading: boolean;
}) {
  return (
    <div className="page-content">
      <Notice />
      <Card
        title="Model identity & readiness"
        eyebrow="From GET /model/info"
        action={
          <Badge tone={info?.model_ready ? "good" : "warning"}>
            {loading
              ? "Checking"
              : info?.model_ready
                ? "Demo ready"
                : "Unavailable"}
          </Badge>
        }
      >
        {info ? (
          <>
            <div className="grid gap-5 sm:grid-cols-3">
              <div>
                <p className="eyebrow">MODEL VERSION</p>
                <p className="identity-value">{info.model_version}</p>
              </div>
              <div>
                <p className="eyebrow">FROZEN THRESHOLD</p>
                <p className="identity-value">{info.threshold.toFixed(2)}</p>
              </div>
              <div>
                <p className="eyebrow">OPERATIONAL VALIDATION</p>
                <p className="identity-value text-amber-800">Not validated</p>
              </div>
            </div>
            <p className="muted text-sm mt-5">
              Readiness: {info.readiness_status.replaceAll("_", " ")}
              {info.unavailable_reason
                ? ` · ${info.unavailable_reason.replaceAll("_", " ")}`
                : ""}
            </p>
            <h3 className="mt-6 mb-3">Approved inputs</h3>
            <div className="flex flex-wrap gap-2">
              {info.approved_features.map((feature) => (
                <span className="feature-tag" key={feature}>
                  {feature}
                </span>
              ))}
            </div>
            <ul className="warning-list">
              {info.limitations.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </>
        ) : (
          <p role="status" className="muted">
            {loading
              ? "Loading the actual model contract…"
              : error || "Model information unavailable. Check System Status."}
          </p>
        )}
      </Card>
      <div className="section-heading">
        <div>
          <p className="eyebrow">FROZEN HISTORICAL SNAPSHOT</p>
          <h2>Final test performance</h2>
        </div>
        <DocLink file="TRAINING.md">Evaluation source</DocLink>
      </div>
      <Metrics />
      <div className="grid gap-5 xl:grid-cols-2">
        <Card
          title="The all-late prediction problem"
          eyebrow="Final test · 13,071 orders"
        >
          <p className="muted text-sm">
            At threshold 0.40, every test order was predicted late. Recall is
            100% because the model flags everything; 5,547 not-late orders
            become false alarms. This operating point offers no selective-alert
            advantage over always-late.
          </p>
          <div className="confusion-grid">
            {evaluation.confusion.map((item) => (
              <div key={item.label}>
                <span>{item.label}</span>
                <strong>{item.value.toLocaleString()}</strong>
              </div>
            ))}
          </div>
          <p className="chart-note">
            Counts from the original held-out evaluation. No new test
            predictions. Late is the positive class.
          </p>
        </Card>
        <Importance />
      </div>
      <Card
        title="Candidate comparison"
        eyebrow="Validation only · 9,497 orders"
        action={<Badge>Historical</Badge>}
      >
        <div
          className="table-scroll"
          tabIndex={0}
          role="region"
          aria-label="Validation candidate comparison"
        >
          <table>
            <caption className="sr-only">
              Historical validation metrics at each candidate’s selected
              threshold. Not live performance.
            </caption>
            <thead>
              <tr>
                {[
                  "Candidate",
                  "Threshold",
                  "Precision",
                  "Recall",
                  "F1",
                  "ROC-AUC",
                ].map((label) => (
                  <th key={label} scope="col">
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {evaluation.candidates.map((row) => (
                <tr key={row.name}>
                  <th scope="row">
                    {row.name}
                    {row.name === "Random Forest" && (
                      <span className="selected-tag">Selected</span>
                    )}
                  </th>
                  <td>{row.threshold}</td>
                  <td>{row.precision}</td>
                  <td>{row.recall}</td>
                  <td>{row.f1}</td>
                  <td>{row.auc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="chart-note">
          Selection used validation F1, then PR-AUC and simplicity to break
          ties. Validation was reused for exploratory investigation; it is not a
          fresh independent assessment.
        </p>
      </Card>
      <Card title="Why v1 remains educational">
        <div className="grid gap-6 md:grid-cols-3">
          <div>
            <span className="number-step">01</span>
            <h3>Shipping plans dominate</h3>
            <p className="muted text-sm mt-2">
              Mode and scheduled days contribute about 98.4% of forest impurity
              importance. Within-mode ranking is near chance.
            </p>
          </div>
          <div>
            <span className="number-step">02</span>
            <h3>Historical data has limits</h3>
            <p className="muted text-sm mt-2">
              Retail data from 2015–2018, uncertain label timing, geographic
              shift and future cancellation exclusions limit generalization.
            </p>
          </div>
          <div>
            <span className="number-step">03</span>
            <h3>Fresh evidence is needed</h3>
            <p className="muted text-sm mt-2">
              Operational use needs suitable new signals, explicit alert costs
              and a fresh prospective evaluation. V1 and its test results remain
              frozen.
            </p>
          </div>
        </div>
        <div className="mt-6">
          <DocLink file="MODEL_QUALITY.md">
            Read the quality investigation
          </DocLink>
        </div>
      </Card>
    </div>
  );
}
