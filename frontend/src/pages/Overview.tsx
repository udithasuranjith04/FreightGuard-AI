import {
  ArrowRight,
  ArrowUpRight,
  FlaskConical,
  Layers3,
  ShieldCheck,
} from "lucide-react";
import { Badge, Card, DocLink, Notice } from "../components/ui";
import { evaluation } from "../evaluation";
import type { SystemState } from "../useSystem";

export function Metrics() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {evaluation.metrics.map((metric) => (
        <Card key={metric.label}>
          <div className="metric-top">
            <span>{metric.label}</span>
            <span className="mini-label">TEST</span>
          </div>
          <p className="metric-value">{metric.value}</p>
          <p className="muted text-sm">{metric.detail}</p>
        </Card>
      ))}
    </div>
  );
}
export function Importance() {
  return (
    <Card
      title="What drives the model?"
      eyebrow="Historical feature importance"
      action={<Layers3 className="muted" size={20} />}
    >
      <p className="muted mb-6 text-sm">
        Shipping-plan inputs dominate the frozen forest.
      </p>
      <div className="space-y-6">
        {evaluation.importance.map((item, i) => (
          <div key={item.label}>
            <div className="mb-2 flex justify-between gap-3 text-sm">
              <span>{item.label}</span>
              <strong>{item.value}%</strong>
            </div>
            <div className="bar-track">
              <div
                className={`bar-fill bar-${i}`}
                style={{ width: `${item.value}%` }}
              />
            </div>
          </div>
        ))}
      </div>
      <p className="chart-note">
        Impurity importance · associations, not causes. Correlated inputs can
        share importance.
      </p>
      <DocLink file="TRAINING.md">Read the frozen evaluation</DocLink>
    </Card>
  );
}
export function Overview({ system }: { system: SystemState }) {
  return (
    <div className="page-content">
      <div className="hero">
        <div className="hero-copy">
          <span className="hero-kicker">
            <FlaskConical size={15} /> THE EDUCATIONAL WORKSPACE
          </span>
          <h2>
            Understand risk.
            <br />
            <span>Know the limits.</span>
          </h2>
          <p>
            Explore shipment delay prediction with a transparent view of what
            the model learned — and what it didn’t.
          </p>
          <a className="button" href="#prediction">
            Explore a shipment <ArrowRight size={17} />
          </a>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />
          <span className="route-node node-one" />
          <span className="route-node node-two" />
          <span className="route-node node-three" />
          <ShieldCheck size={66} strokeWidth={1.2} />
          <span className="visual-caption">FROZEN MODEL / V1</span>
        </div>
      </div>
      <Notice />
      <div className="section-heading">
        <div>
          <p className="eyebrow">HISTORICAL EVALUATION</p>
          <h2>A clear view of model performance</h2>
        </div>
        <span className="muted text-sm">
          Final test · {evaluation.testOrders.toLocaleString()} orders · 28 Oct
          2026
        </span>
      </div>
      <Metrics />
      <div className="grid gap-5 xl:grid-cols-[1.15fr_1fr]">
        <Importance />
        <Card
          title="Your system, at a glance"
          eyebrow="Actual API status"
          action={
            <a
              aria-label="View system status"
              className="icon-button"
              href="#status"
            >
              <ArrowUpRight size={20} />
            </a>
          }
        >
          <div className="status-row">
            <div>
              <strong>FastAPI backend</strong>
              <p className="muted text-sm">Application health endpoint</p>
            </div>
            <Badge
              tone={system.loading ? "neutral" : system.health ? "good" : "bad"}
            >
              {system.loading
                ? "Checking"
                : system.health
                  ? "Connected"
                  : "Unavailable"}
            </Badge>
          </div>
          <div className="status-row">
            <div>
              <strong>Frozen model v1</strong>
              <p className="muted text-sm">Trusted local artifact</p>
            </div>
            <Badge tone={system.info?.model_ready ? "good" : "warning"}>
              {system.loading
                ? "Checking"
                : system.info?.model_ready
                  ? "Demo ready"
                  : "Not ready"}
            </Badge>
          </div>
          <div className="status-row">
            <div>
              <strong>Operational validation</strong>
              <p className="muted text-sm">Real-world order-specific alerts</p>
            </div>
            <Badge tone="warning">Not validated</Badge>
          </div>
          <div className="subtle-box mt-5">
            <p className="text-sm">
              No live shipments are connected. Performance figures are a
              documented historical snapshot, not operational KPIs.
            </p>
          </div>
        </Card>
      </div>
      <p className="source-note">
        Source: frozen v1 evaluation, documented in{" "}
        <DocLink file="TRAINING.md">TRAINING.md</DocLink>. No new test
        evaluation has been run.
      </p>
    </div>
  );
}
