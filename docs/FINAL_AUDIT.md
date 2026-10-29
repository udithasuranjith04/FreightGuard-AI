# FreightGuard AI v1 final release audit

Verdict: **READY FOR EDUCATIONAL PORTFOLIO RELEASE** for the native/local
application and its source checkpoint. This is not approval of public hosting,
container distribution, operational alerts, or dataset/model redistribution.
The user authorized the Milestone 7 commit if the release-blocking checks pass;
no push, tag or external deployment is authorized.

## Executed verification

| Check | Actual result |
| --- | --- |
| Complete pytest suite | 119 passed, one existing TestClient deprecation warning |
| Full Ruff | Exit 1: only preserved inspect_data.py I001 |
| Maintained-code Ruff with explicit script exclusion | Passed |
| pip check | Passed |
| npm ci | Passed from package-lock.json |
| TypeScript strict checking | Passed |
| Frontend ESLint | Passed, zero lint warnings |
| Vitest unit/UI suite | 38 passed across three files |
| Vite production build | Passed; approximately 354 KB JS / 109 KB gzip, 22 KB CSS |
| Production browser integration | 10 passed, desktop/mobile Chromium |
| Automated accessibility | Axe WCAG A/AA checks on all five pages passed; 320px overflow check passed |
| npm audit | No known vulnerabilities reported |
| Python pip-audit | No known vulnerabilities in 25 runtime and 9 additional dev pins |
| Source/history/public-bundle pattern review | No matches; scanner is limited, not a PII/penetration certification |
| YAML parsing | Compose, model override and CI workflow parsed |
| Documentation links and Git whitespace | Passed |
| Artifact/script preservation | All four original artifact SHA-256 values, script working hash and empty staged blob match |

Live HTTP checks returned 200 for /health, /model/info, /openapi.json, /docs and
/redoc. POST /predict returned 200 with the invented shipment: 4 scheduled days,
Standard Class, Europe, Western Europe, Francia. Its score was
0.4272314668675644; classification Late, frozen threshold 0.40, experimental true
and operationally_validated false. An extra synthetic Customer Email field
returned 422 without echoing its value. Browser tests verify all advertised pages,
exactly five submitted fields, historical metrics, API failures and actual status.

Port 5173 already hosted a development server and was left untouched. The audit
used production preview on 5174 and an explicitly allowed temporary CORS origin.
PLAYWRIGHT_BASE_URL now allows this without changing the normal 5173 default.
Only audit-owned servers were stopped. No real dataset/model training command,
diagnostic run or held-out cohort evaluation was performed. Tests use synthetic
fixtures; no frozen artifact or threshold was modified.

## Final audit corrections

Added .env.* ignore coverage outside the frontend. The documented no-trust startup
now explicitly sets FREIGHTGUARD_TRUST_LOCAL_MODEL=false, so an inherited shell
setting cannot contradict its description. Added a configurable browser-test URL
to avoid interrupting an existing local frontend. No other application bug was
found during this final pass.

## Remaining warnings and limits

- inspect_data.py retains its existing import-layout warning by explicit user
  instruction. Its staged and working versions must remain unchanged and outside
  the Milestone 7 commit. This exception is not hidden as a clean full Ruff run.
- Existing Starlette/HTTPX deprecation, ESLint 9 support notice, Zod PURE-comment
  annotations, npm lifecycle-script notices and NO_COLOR/FORCE_COLOR warnings
  remain. pip-audit advises adding distribution hashes to Python pins.
- Docker is not installed here. Docker builds, compose config/runtime, Nginx
  runtime headers, image scans and fresh Linux installation were not executed.
  Remote GitHub Actions was not run; no remote action was triggered. YAML parsing
  does not validate container behavior. Mutable image/action tags need review.
- Exact Python pins snapshot this environment; they are not hash-locked or a
  verified cross-platform lock. Only the existing environment and clean npm
  installation were exercised. No fresh Python environment reproduction claim.
- Manual screen-reader and non-Chromium review remain open.
- Source license choice, dataset provenance/license and artifact distribution
  rights remain open. No raw data or fitted artifacts are included in Git.
- No TLS/authentication/rate-limit production hosting controls are provided.
  Local-only CORS is not authorization. External hosting needs separate approval.
- V1 predicts every test order late at 0.40 and has near-chance supported
  within-shipping-mode ranking. Its scores are experimental and conditional on
  non-cancellation. It is not operationally validated or a delivery guarantee.

## 2026-10-30 release-preparation update

The user authorized correcting author and committer metadata on the nine local
commits after the unchanged `origin/main` base. A backup ref was created; each
rewritten commit retained its original tree and message, and the two commits on
`origin/main` were not rewritten. A scoped MIT license was added for original
application source code only. The DataCo source URL, version, checksum, and
redistribution terms remain unverified; no dataset or serialized model artifacts
are included or covered by that license. Third-party dependencies retain their
own licenses. The two already-published commits still contain the earlier
machine-local author/committer identity and require user review before making the
repository public.

These are explicit limits/gates for other release targets, not claims that those
checks passed. See RELEASE_CHECKLIST.md and DEPLOYMENT.md before distribution or
hosting. See README.md for the verified native startup commands. The commit hash
is recorded in Git history and the final audit handoff; no self-referential hash
is embedded in committed content.
