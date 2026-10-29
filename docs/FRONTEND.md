# FreightGuard AI dashboard (Milestone 6)

A local React + strict TypeScript + Vite + Tailwind CSS dashboard. It serves the
existing educational v1 API without changing the model, threshold, or test result.
No live shipments, fabricated analytics, customer records, login or backend storage.

## Run both applications

Use Python 3.12 and Node >=22.12 (verified with Node 24.20.0). From the repository
root, terminal 1:

```sh
source .venv/bin/activate
python -m pip install -e '.[dev]'
shasum -a 256 data/processed/models/v1/pipeline.joblib
export FREIGHTGUARD_TRUST_LOCAL_MODEL=true
export FREIGHTGUARD_MODEL_SHA256=e3d46fa78998d13584ed7d7ea88bd321c69e2773aa9b6f18eab20eee73d0ddef
python -m uvicorn freightguard.api.app:app --host 127.0.0.1 --port 8000 --no-access-log
```

Only trust the locally produced, reviewed artifact. Compare the hash with the
recorded original identity before starting. Fresh-checkout artifact generation
and unavailable-model behavior are documented in [API.md](API.md). Never delete
an existing frozen run, refit or retest merely to run the dashboard.

Terminal 2, also from the repository root:

```sh
cd frontend
npm ci
cp .env.example .env.local
npm run dev
```

Open <http://127.0.0.1:5173>. Vite uses strict port 5173, one of the API's explicit
allowed development origins. `VITE_API_BASE_URL` defaults to
`http://127.0.0.1:8000`; set it in `frontend/.env.local` and restart Vite to change
it. This value is compiled into browser code. Never put credentials, artifact
paths, model checksums/trust controls or secrets in frontend environment files.
CORS failures may look like network failures; review backend origin configuration.

Swagger UI: <http://127.0.0.1:8000/docs>. To view the production bundle locally:

```sh
cd frontend
npm run build
npm run preview
```

Both Vite and its preview bind to loopback. Stop servers with Ctrl+C. Public
hosting, TLS, authentication, rate limits and operational validation are deferred.

## Pages

- Overview: product introduction, actual backend/model availability and explicitly
  historical final-test metrics. Feature-importance chart has visible values.
- Shipment Prediction: exactly five required inputs, typed POST /predict,
  runtime schema checking, field validation, loading/error/unavailable/empty/result
  states, reset and stale-result clearing on input edits. No request persistence.
- Model Insights: identity, approved inputs, readiness and limitations from
  GET /model/info; historical validation table, final-test confusion counts,
  feature-importance bars and transparent all-late explanation.
- System Status: independent GET /health and GET /model/info checks, explicit
  connection versus model availability, timestamps, manual refresh and 60-second
  rechecks. A network failure includes possible CORS/configuration causes.
- About & Documentation: purpose, data contract, architecture and links to public
  Markdown project documents. Links open raw Markdown docs in a new tab, announced
  accessibly. No repository browser or arbitrary file-serving endpoint is added.

Navigation uses URL hashes and browser back/forward. Mobile has an accessible
collapsible navigation, visible focus states and a skip link. Forms use native
labels/selects and inline error descriptions. Results use a live region and focus
moves to the result; reduced motion is respected. A horizontal table scroll area
keeps small screens usable without losing data.

## Data integrity and contract

`src/api.ts` mirrors the actual Pydantic names, with Zod validating responses at
runtime; incompatible v1/threshold/operational-validation responses fail visibly.
Requests reject extras, invalid types, days outside integer 0–4 and unsupported
categories. Category dropdowns come from the loaded model's training vocabulary,
including original spellings such as Francia. Broad geography syntax matches
backend validation; geography/service combinations are not cross-validated.
Requests time out after 12 seconds. Errors use fixed public messages rather than
echoing arbitrary server strings. No browser request logging, analytics or local
storage is used. Model load failures leave historical documentation available.

`src/evaluation.ts` contains only manually transcribed public aggregate figures
from [TRAINING.md](TRAINING.md), frozen 2026-10-28. These are not API telemetry and
remain labeled historical even when the backend is offline. The API has no metrics
endpoint; none was invented. No generated artifact is copied into the frontend.
`vite.config.ts` serves/bundles only five explicitly allowed documentation files.

## Check the implementation

From `frontend/`:

```sh
npm run typecheck
npm run lint
npm test
npm run build
```

Backend regression checks, from the repository root:

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
```

Full Ruff still reports the preserved inspection-script import issue; new API
code is clean. For browser integration tests, start both servers above, then:

```sh
cd frontend
npx playwright install chromium
npm run test:e2e
```

The browser tests run the real synthetic prediction at desktop/mobile widths,
assert the five-field request, visible result and honest labels, actual ready
status, no horizontal page overflow and no browser errors. They do not read raw
data or score the held-out cohort. Test screenshots/traces are ignored.

Synthetic shipment: 4 scheduled days, Standard Class, Europe, Western Europe,
Francia. On the original frozen artifact the expected score is approximately
0.4272314668675644 (42.7% display), experimental classification Late at 0.40.
The UI explains that this is not a validated probability or delivery guarantee.

## Maintenance

`components/ui.tsx` holds shared cards/buttons/badges/notices; pages are separate
modules. `styles.css` contains the theme/component rules and responsive layout,
with Tailwind utilities for grids/spacing. Lucide provides consistent icons.
Zod checks the network boundary; Vitest, Testing Library and Playwright cover
behavior. ESLint and TypeScript check the source; `package-lock.json` pins the
resolved npm tree for `npm ci`. No state framework, router service, chart runtime,
database or new Python dependency is needed for this milestone.

Known limits: v1 is not operationally validated, its cutoff flags every test order,
within-mode ranking is near chance, the dataset is old retail data and future
cancellation exclusion is retrospective. Status checks are snapshots, not uptime
monitoring. Frontend tests use invented fixtures; browser tests require local
servers and the explicitly trusted original artifact. This is not a full manual
screen-reader or cross-browser certification.


## Verified results

29 frontend tests, strict TypeScript, ESLint and production build pass. Six
Chromium desktop/mobile browser checks pass, including actual synthetic prediction
and injected unavailable states. Backend regression: 112 tests pass. npm audit:
zero vulnerabilities in the locked tree. Full Ruff retains only the existing
inspect_data.py I001. Known non-failing messages include the installed ESLint 9
version-support deprecation, Zod PURE-comment build annotations and the existing
Starlette/HTTPX TestClient deprecation. See PROGRESS.md for evidence and boundaries.
