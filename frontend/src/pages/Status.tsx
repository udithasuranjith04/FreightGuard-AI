import { Activity, RefreshCw, Server, ShieldCheck } from "lucide-react";
import { API_BASE } from "../api";
import { Badge, Button, Card } from "../components/ui";
import type { SystemState } from "../useSystem";
export function Status({
  system,
  refresh,
}: {
  system: SystemState;
  refresh: () => Promise<void>;
}) {
  const connected = system.health !== null;
  const ready =
    system.info?.model_ready === true && system.health?.model_ready === true;
  return (
    <div className="page-content">
      <div className="status-banner">
        <Activity size={25} />
        <div>
          <h2>
            {system.loading
              ? "Checking your local system…"
              : !connected
                ? "Backend unavailable"
                : ready
                  ? "Ready for educational inference"
                  : "Backend connected · model not ready"}
          </h2>
          <p>
            {system.loading
              ? "Requesting health and model information."
              : !connected
                ? "Start the FastAPI backend, then refresh this check."
                : ready
                  ? "The backend and frozen artifact are responding. Operational validation remains false."
                  : "Application health and model readiness are separate. Check the artifact trust, checksum and local file."}
          </p>
        </div>
        <Button
          secondary
          onClick={() => {
            void refresh();
          }}
          disabled={system.loading}
        >
          <RefreshCw
            size={16}
            className={system.loading ? "animate-spin" : ""}
          />
          Refresh status
        </Button>
      </div>
      <div className="grid gap-5 md:grid-cols-2">
        <Card
          title="Application health"
          eyebrow="GET /health"
          action={<Server size={21} className="muted" />}
        >
          <Badge tone={system.loading ? "neutral" : connected ? "good" : "bad"}>
            {system.loading
              ? "Checking"
              : connected
                ? "Connected"
                : "Unavailable"}
          </Badge>
          <p className="muted mt-5">
            {system.health
              ? `Application status: ${system.health.status}. Model readiness reported by health: ${system.health.model_ready ? "ready" : "unavailable"}.`
              : system.healthError || "Waiting for a response."}
          </p>
        </Card>
        <Card
          title="Model readiness"
          eyebrow="GET /model/info"
          action={<ShieldCheck size={21} className="muted" />}
        >
          <Badge tone={system.loading ? "neutral" : ready ? "good" : "warning"}>
            {system.loading
              ? "Checking"
              : ready
                ? "Educational demo ready"
                : "Unavailable"}
          </Badge>
          <p className="muted mt-5">
            {system.info
              ? `Model ${system.info.model_version} · ${system.info.readiness_status.replaceAll("_", " ")}. ${system.info.unavailable_reason ? `Reason: ${system.info.unavailable_reason.replaceAll("_", " ")}.` : "Trusted artifact loaded during application startup."}`
              : system.infoError || "Waiting for model information."}
          </p>
        </Card>
      </div>
      <Card title="Connection details">
        <dl className="details-list">
          <div>
            <dt>API base URL</dt>
            <dd className="break-all">{API_BASE}</dd>
          </div>
          <div>
            <dt>Last completed check</dt>
            <dd>
              {system.checkedAt
                ? system.checkedAt.toLocaleTimeString()
                : "Not checked yet"}
            </dd>
          </div>
          <div>
            <dt>Refresh policy</dt>
            <dd>On load, every 60 seconds, and on request</dd>
          </div>
          <div>
            <dt>Operational validation</dt>
            <dd>Not validated</dd>
          </div>
        </dl>
        <a
          className="text-link mt-5"
          href={`${API_BASE}/docs`}
          target="_blank"
          rel="noreferrer"
        >
          Open interactive API documentation
          <span className="sr-only"> (opens in a new tab)</span> ↗
        </a>
      </Card>
      <Card title="If predictions are unavailable">
        <ol className="troubleshooting">
          <li>
            Start the backend on the configured API URL. A connection failure
            can also mean CORS or network settings need attention.
          </li>
          <li>
            If the backend is connected but the model is unavailable, review
            local artifact trust, the verified SHA-256 and file availability.
            Restart the backend after changes.
          </li>
          <li>
            Keep secrets and model trust settings on the backend. Frontend
            environment variables are public browser configuration.
          </li>
        </ol>
      </Card>
    </div>
  );
}
