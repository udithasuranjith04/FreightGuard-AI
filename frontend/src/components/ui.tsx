import type { ButtonHTMLAttributes, ReactNode } from "react";
import { AlertTriangle, ArrowUpRight } from "lucide-react";

export function Card({
  title,
  eyebrow,
  action,
  children,
  className = "",
}: {
  title?: string;
  eyebrow?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`card ${className}`}>
      {(title || action) && (
        <div className="card-heading">
          <div>
            {eyebrow && <p className="eyebrow">{eyebrow}</p>}
            {title && <h2>{title}</h2>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}
export function Button({
  children,
  secondary = false,
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { secondary?: boolean }) {
  return (
    <button
      className={`button ${secondary ? "button-secondary" : ""} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "good" | "warning" | "neutral" | "bad";
}) {
  return (
    <span className={`badge badge-${tone}`}>
      <span aria-hidden="true" className="status-dot" />
      {children}
    </span>
  );
}
export function Notice({
  title = "Educational model · Not operationally validated",
  children,
}: {
  title?: string;
  children?: ReactNode;
}) {
  return (
    <aside className="notice">
      <AlertTriangle size={19} aria-hidden="true" />
      <div>
        <strong>{title}</strong>
        <p>
          {children ??
            "V1 mainly learns shipping-plan patterns. Its frozen threshold predicted every test order late. Use this dashboard to explore the model, not to prioritize real shipments."}
        </p>
      </div>
    </aside>
  );
}
export function DocLink({
  file,
  children,
}: {
  file: string;
  children: ReactNode;
}) {
  return (
    <a
      className="text-link"
      href={`/docs/${file}`}
      target="_blank"
      rel="noreferrer"
    >
      {children}
      <ArrowUpRight size={15} aria-hidden="true" />
      <span className="sr-only"> (opens in a new tab)</span>
    </a>
  );
}
