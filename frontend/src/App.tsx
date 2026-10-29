import { useEffect, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  BookOpen,
  ChevronRight,
  FlaskConical,
  LayoutDashboard,
  Menu,
  ScanLine,
  ShieldCheck,
  SlidersHorizontal,
  X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Badge } from "./components/ui";
import { Overview } from "./pages/Overview";
import { Prediction } from "./pages/Prediction";
import { Insights } from "./pages/Insights";
import { Status } from "./pages/Status";
import { About } from "./pages/About";
import { useSystem } from "./useSystem";
const navigation: {
  id: string;
  name: string;
  title: string;
  description: string;
  icon: LucideIcon;
}[] = [
  {
    id: "overview",
    name: "Overview",
    title: "Overview",
    description: "A transparent view of shipment risk intelligence.",
    icon: LayoutDashboard,
  },
  {
    id: "prediction",
    name: "Shipment Prediction",
    title: "Shipment Risk Prediction",
    description: "Explore the frozen model with five approved inputs.",
    icon: ScanLine,
  },
  {
    id: "insights",
    name: "Model Insights",
    title: "Model Insights",
    description:
      "The evidence behind the model. The limits behind the numbers.",
    icon: SlidersHorizontal,
  },
  {
    id: "status",
    name: "System Status",
    title: "API & System Status",
    description: "Real connectivity. Explicit model readiness.",
    icon: Activity,
  },
  {
    id: "about",
    name: "About & Documentation",
    title: "About FreightGuard AI",
    description: "The project, the architecture and the learning journey.",
    icon: BookOpen,
  },
];
function currentPage() {
  return window.location.hash.slice(1) || "overview";
}
export default function App() {
  const [page, setPage] = useState(currentPage);
  const [menu, setMenu] = useState(false);
  const system = useSystem();
  const selected = navigation.find((item) => item.id === page);
  useEffect(() => {
    const change = () => {
      setPage(currentPage());
      setMenu(false);
      document.getElementById("page-title")?.focus();
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", change);
    return () => window.removeEventListener("hashchange", change);
  }, []);
  useEffect(() => {
    document.title = `${selected?.title || "Page not found"} · FreightGuard AI`;
  }, [selected]);
  return (
    <div className="app-shell">
      <a
        className="skip-link"
        href="#main-content"
        onClick={(event) => {
          event.preventDefault();
          document.getElementById("main-content")?.focus();
        }}
      >
        Skip to content
      </a>
      <aside className="sidebar">
        <a href="#overview" className="brand">
          <span className="brand-symbol">
            <ShieldCheck size={26} />
          </span>
          <span>
            FreightGuard <b>AI</b>
            <small>LOGISTICS INTELLIGENCE</small>
          </span>
        </a>
        <button
          className="mobile-menu icon-button"
          aria-label={menu ? "Close navigation" : "Open navigation"}
          aria-expanded={menu}
          aria-controls="primary-navigation"
          onClick={() => setMenu(!menu)}
        >
          {menu ? <X /> : <Menu />}
        </button>
        <div
          className={`sidebar-content ${menu ? "is-open" : ""}`}
          id="primary-navigation"
        >
          <p className="nav-label">WORKSPACE</p>
          <nav aria-label="Main navigation">
            {navigation.map(({ id, name, icon: Icon }) => (
              <a
                key={id}
                href={`#${id}`}
                aria-current={page === id ? "page" : undefined}
              >
                <Icon size={19} />
                <span>{name}</span>
                {page === id && (
                  <ChevronRight size={15} className="nav-chevron" />
                )}
              </a>
            ))}
          </nav>
          <div className="sidebar-footer">
            <div className="sidebar-note">
              <FlaskConical size={21} />
              <strong>Built for exploration.</strong>
              <p>
                Educational model. Transparent limitations. No operational
                guarantees.
              </p>
              <a href="#insights">
                Understand model v1 <ArrowUpRight size={15} />
              </a>
            </div>
            <p className="sidebar-version">
              <span className="status-dot" />
              FROZEN V1 <span>RESEARCH EDITION</span>
            </p>
          </div>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <ChevronRight size={14} />
            <span>{selected?.name || "Not found"}</span>
          </div>
          <a className="status-link" href="#status">
            <Badge
              tone={system.loading ? "neutral" : system.health ? "good" : "bad"}
            >
              {system.loading
                ? "Checking API"
                : system.health
                  ? "API connected"
                  : "API unavailable"}
            </Badge>
          </a>
        </header>
        <main id="main-content" tabIndex={-1}>
          <div className="page-header">
            <div>
              <p className="eyebrow">FREIGHTGUARD AI / WORKSPACE</p>
              <h1 id="page-title" tabIndex={-1}>
                {selected?.title || "Page not found"}
              </h1>
              <p>
                {selected?.description ||
                  "Choose a page from the navigation to continue."}
              </p>
            </div>
            <Badge tone="warning">
              <FlaskConical size={13} />
              Educational demo
            </Badge>
          </div>
          {page === "overview" ? (
            <Overview system={system} />
          ) : page === "prediction" ? (
            <Prediction info={system.info} loading={system.loading} />
          ) : page === "insights" ? (
            <Insights
              info={system.info}
              error={system.infoError}
              loading={system.loading}
            />
          ) : page === "status" ? (
            <Status system={system} refresh={system.refresh} />
          ) : page === "about" ? (
            <About />
          ) : (
            <a className="button" href="#overview">
              Return to Overview
            </a>
          )}
        </main>
        <footer className="workspace-footer">
          <span>
            FreightGuard AI{" "}
            <span className="muted">/ Educational logistics intelligence</span>
          </span>
          <span>Frozen model v1 · Not operationally validated</span>
        </footer>
      </div>
    </div>
  );
}
