# Security and privacy review — 2026-10-29

Scope: local source, reachable Git file history, synthetic tests, built frontend,
API validation/loading/logging paths, npm dependencies and pinned Python packages.
This is release preparation, not a penetration test, compliance certification or
proof that every possible secret/personal value is absent.

## Findings and fixes

- Requests require precisely five fields. Extra sensitive/identifier/outcome fields
  fail without being echoed. Bounded integer days and supported categories are
  enforced; all loaded categorical vocabularies must now have the expected shape.
  Truncated vocabulary artifacts no longer leave a model deceptively ready.
- Loading requires explicit local trust and a checked SHA-256 before joblib
  deserialization; the same verified bytes are loaded. A new API regression test
  proves checksum mismatch never calls the deserializer. No uploads supported.
- Unexpected API failures previously lost CORS response headers at the outer error
  boundary. The fix preserves only explicitly allowed origins on 500 responses.
  Error JSON and logs omit request/exception details. Tests cover approved and
  unapproved origins, validation errors and deliberate private canary strings.
- API responses now include no-store, nosniff and no-referrer headers. Stack traces
  and filesystem paths are not returned. Documented startup disables access logs.
- Frontend success responses are runtime checked. Scores/classifications must now
  agree with the frozen >=0.40 rule; the frontend does not relabel model results.
  Invalid API URLs fail with safe configuration messages rather than import-time
  crashes. URLs with credentials/query/fragment are rejected, not rendered.
- Automated accessibility found low-contrast secondary text; foregrounds were
  darkened and fade opacity removed. Axe WCAG A/AA checks now pass across all five
  pages at desktop/mobile sizes. This does not certify every accessibility need.
- Docker candidates use an allowlisted context, no artifact/image embedding,
  non-root processes, loopback host ports, dropped capabilities and read-only
  roots. They remain unverified until Docker builds/runtime/image scans occur.

## Dependency checks

`npm audit --json` found zero known vulnerabilities. Python `pip-audit` checked
25 runtime pins and 9 additional test/development pins separately, also with no
known vulnerabilities. The audit tool was installed in a temporary isolated venv;
the project's existing environment was not changed. Reproduce with a separate
audit environment containing pip-audit:

```sh
python -m pip_audit -r requirements/runtime.txt --no-deps --disable-pip --progress-spinner off
python -m pip_audit -r requirements/dev.txt --no-deps --disable-pip --progress-spinner off
```

The runtime file is audited separately because the observed dev audit output
listed the nine additional pins rather than all nested requirements. `--no-deps`
audits supplied exact versions without changing/resolving the working environment.
Runtime/test dependency closure is recorded from the existing interpreter, and
`pip check` passed. These snapshots lack hashes and are not platform-independent
lockfiles. Audit results are time-specific and do not cover unknown flaws, base
images, operating systems, or an untested deployment.

Known non-failing tooling messages: ESLint 9's upstream version-support notice;
Starlette/HTTPX TestClient deprecation; Zod PURE-comment build annotations;
NO_COLOR/FORCE_COLOR precedence; npm lifecycle-script-policy notices. No automatic
force-upgrade was used. An unsupported tool version still merits maintenance
review, even when no known advisory is reported.

## Source/history/public artifact review

Run `.venv/bin/python scripts/audit_repository.py` from the repository root. It
checks all reachable Git blobs, current non-ignored files and frontend/dist for
known key/token/literal-credential/email patterns, and historic private data/env
paths. It emits only counts, path and pattern names, never matching values. The
scan found no matches. Synthetic example-domain contacts are intentionally allowed;
test fixture canaries are invented. No raw data/model files have been tracked in
reachable history; currently only data/.gitkeep placeholders are tracked.

The scanner is deliberately small and cannot identify arbitrary names, addresses,
encoded secrets or all credential formats. Manual source/log-path review found no
customer records or real credentials introduced by this work. Source field names
such as Customer Email in rejection tests/documentation are not customer values.
Git author metadata was not classified as customer data or rewritten. No raw
private dataset was scanned or printed. No request payloads are logged. Dependency
install logs contain package metadata, not application customer data. Tests assert
that deliberate private canaries do not reach application responses/log output.
Review generated screenshots before publishing; none was added to Git.

## Boundaries and remaining gates

- No authentication, TLS termination, rate limiting or public hosting is provided.
  CORS is not authorization. Keep native servers and sample Compose ports local.
- Public browser environment variables are not secrets. Do not inject credentials
  into VITE variables, source, URLs, container args or screenshots.
- Native server docs may load Swagger UI assets from a CDN; the dashboard itself
  uses bundled code/icons and system fonts. Offline interactive API docs are not
  guaranteed by this milestone.
- Docker, image scanning and remote CI could not be executed here. Base-image and
  GitHub Action tags remain mutable; review/pin exact identities before release.
- No source license has been chosen; dataset provenance/license and artifact
  redistribution require review before distribution.
- V1's all-late test result and near-chance within-mode ranking block operational
  claims. A new prospective modeling evaluation needs separate authorization.

See DEPLOYMENT.md and RELEASE_CHECKLIST.md. Do not externally deploy or make a
final release commit/tag without the user's review and explicit authorization.
