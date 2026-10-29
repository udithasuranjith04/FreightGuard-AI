import {
  ArrowRight,
  BookOpen,
  Database,
  Layers3,
  ShieldCheck,
} from "lucide-react";
import { Card, DocLink, Notice } from "../components/ui";
export function About() {
  return (
    <div className="page-content">
      <div className="about-intro">
        <span className="eyebrow">BUILT TO MAKE THE LEARNING VISIBLE</span>
        <h2>
          Logistics intelligence.
          <br />
          With honest boundaries.
        </h2>
        <p>
          FreightGuard AI is a portfolio project exploring shipment delay
          prediction — from a safe data contract to a reproducible model,
          trusted inference API and accessible dashboard.
        </p>
      </div>
      <Notice />
      <div className="grid gap-5 md:grid-cols-3">
        {[
          {
            Icon: Database,
            title: "A conservative data contract",
            text: "DataCo Smart Supply Chain historical retail data. One non-canceled order at finalized checkout shipping-plan time. Only five inputs; personal information and delivery outcomes are excluded.",
          },
          {
            Icon: Layers3,
            title: "A reproducible experiment",
            text: "Chronological training, validation and final test partitions with seven-day gaps. Training-only preprocessing. Fixed candidates, seed 42 and validation selection; final test evaluated once.",
          },
          {
            Icon: ShieldCheck,
            title: "A transparent demonstration",
            text: "The frozen v1 model and threshold stay unchanged. Every prediction is experimental. No live shipment tracking, customer records, operational KPIs or real-world accuracy claims.",
          },
        ].map(({ Icon, title, text }) => (
          <Card key={title}>
            <span className="about-icon">
              <Icon size={23} />
            </span>
            <h2 className="mt-4 mb-3">{title}</h2>
            <p className="muted text-sm">{text}</p>
          </Card>
        ))}
      </div>
      <Card
        title="How the application fits together"
        eyebrow="Local architecture"
      >
        <div className="architecture-flow">
          <div>
            <strong>React + TypeScript</strong>
            <span>Accessible dashboard</span>
          </div>
          <ArrowRight aria-hidden="true" />
          <div>
            <strong>FastAPI + Pydantic</strong>
            <span>Validated REST contract</span>
          </div>
          <ArrowRight aria-hidden="true" />
          <div>
            <strong>Frozen scikit-learn v1</strong>
            <span>Trusted, checksum-verified</span>
          </div>
        </div>
        <p className="chart-note">
          Prediction requests contain only the five approved fields. The API
          loads the model once at startup. The dashboard neither loads
          serialized models nor needs raw datasets.
        </p>
      </Card>
      <Card
        title="Project documentation"
        action={<BookOpen size={20} className="muted" />}
      >
        <div className="documentation-grid">
          {[
            [
              "FRONTEND.md",
              "Dashboard setup",
              "Local commands, checks and integration notes",
            ],
            [
              "API.md",
              "API reference",
              "Trust settings, endpoint examples and OpenAPI",
            ],
            [
              "TRAINING.md",
              "Model evaluation",
              "Frozen design, historical metrics and test results",
            ],
            [
              "MODEL_QUALITY.md",
              "Quality investigation",
              "Validation-only evidence and operational limitations",
            ],
            [
              "ARCHITECTURE.md",
              "Architecture",
              "Project structure and engineering decisions",
            ],
          ].map(([file, title, description]) => (
            <div key={file}>
              <DocLink file={file!}>{title}</DocLink>
              <p className="muted text-sm mt-1">{description}</p>
            </div>
          ))}
        </div>
      </Card>
      <p className="source-note">
        Dataset provenance, redistribution terms and real operational feature
        availability remain unresolved. Raw data stays local and is never
        included in the frontend build.
      </p>
    </div>
  );
}
