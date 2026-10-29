# Local educational FastAPI backend

Milestone 5 serves the unchanged v1 pipeline and threshold 0.40. This is a locally
working API with production-style validation and error handling, not a validated
operational alert service. No frontend or public deployment is included.

## Install and start (repository root)

```sh
source .venv/bin/activate
python -m pip install -e '.[dev]'
shasum -a 256 data/processed/models/v1/pipeline.joblib
export FREIGHTGUARD_TRUST_LOCAL_MODEL=true
export FREIGHTGUARD_MODEL_SHA256=e3d46fa78998d13584ed7d7ea88bd321c69e2773aa9b6f18eab20eee73d0ddef
python -m uvicorn freightguard.api.app:app --host 127.0.0.1 --port 8000 --no-access-log
```

Only opt in after trusting this locally generated artifact and checking its hash
against the recorded identity above. A checksum does not make an untrusted pickle
safe. Never accept model uploads or automatically deserialize downloaded models.
An independently generated artifact can have a different hash; review its origin
and frozen selection before configuring that identity.

FastAPI/Pydantic provide HTTP routing, OpenAPI, and strict schemas; Uvicorn runs
the server. HTTPX is a test dependency. The existing Python 3.12 environment is
retained. Dependencies remain version ranges, not a reproducibility lockfile.

If artifacts are absent on a fresh checkout, obtain the private dataset separately
and run `python -m freightguard.train_model` following [TRAINING.md](TRAINING.md).
That command trains/evaluates once on a fresh checkout; completed runs only replay
saved results. Never delete this workspace's frozen run or select another path to
retest the original holdout. Without the artifact/trust/hash, the API still starts:
health/info work and prediction returns 503. Restart after correcting configuration;
there is no hot reload of artifacts. Each worker loads once during startup.

## Endpoints and examples

- `GET /health`: application liveness, e.g. `{"status":"ok","model_ready":true}`.
  HTTP 200 does not establish inference readiness; inspect `model_ready`.
- `GET /model/info`: version, threshold, approved features, request field mapping,
  readiness/reason, limitations, and allowed training categories. Category names
  retain original dataset spellings (for example `Francia`, not `France`). When
  unavailable the category lists are empty. No paths or records are returned.
- `POST /predict`: exactly five required fields, one synthetic shipment per call.

```sh
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/model/info
curl -X POST http://127.0.0.1:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"scheduled_shipping_days":4,"shipping_mode":"Standard Class","market":"Europe","order_region":"Western Europe","order_country":"Francia"}'
```

The synthetic example returns (warnings abbreviated here):

```json
{"risk_score":0.4272314668675644,"experimental_prediction":"late","model_version":"v1","threshold":0.4,"experimental":true,"operationally_validated":false,"warnings":["Educational model: primarily shipping-plan patterns, not validated order-specific operational alerts."]}
```

Actual responses also warn about non-cancellation, historical data, and the all-late
test result. The score is experimental, not a calibrated delivery guarantee. V1
primarily learns shipping-plan patterns and its frozen threshold predicted every
test order late. Within-mode ranking is near chance. See [MODEL_QUALITY.md](MODEL_QUALITY.md).

Scheduled days must be an integer 0–4 (the supported educational domain); booleans,
strings, floats, missing/null values fail. Modes and markets use explicit enums;
all categorical inputs must also belong to the loaded training vocabulary.
Country/region strings are bounded and reject contact-detail syntax. Unknown
categories are rejected before prediction, even though the underlying encoder
can represent them. No cross-field geography/service consistency is inferred.
Extra fields, including personal information, IDs, actual durations, and delivery
outcomes, are rejected. Do not send personal information in any field.

Errors consistently use this shape without echoing submitted values/unknown keys:

```json
{"error":{"code":"model_unavailable","message":"Educational model is unavailable; check /model/info.","fields":[]}}
```

Statuses: 422 invalid input/unknown categories, 503 unavailable model, 500 internal
failure, 413 body over 16 KiB, 415 non-JSON content, 404 missing route, 405 wrong
method. Errors omit stack traces and filesystem paths. Operational logs contain
fixed events/reason codes only. The startup command disables access logging so
URLs/query strings cannot accidentally enter server access logs.

Interactive Swagger UI: <http://127.0.0.1:8000/docs>. ReDoc: `/redoc`.
Machine-readable schema: `/openapi.json`.

## Configuration and checks

`FREIGHTGUARD_MODEL_PATH` optionally overrides the local pipeline path.
`FREIGHTGUARD_TRUST_LOCAL_MODEL` defaults to false; `FREIGHTGUARD_MODEL_SHA256`
requires a lowercase SHA-256. Default CORS origins are explicitly
`http://localhost:5173,http://127.0.0.1:5173`. Override with comma-separated
`FREIGHTGUARD_CORS_ORIGINS`; an empty value disables allowed browser origins.
Wildcard origins are rejected. Credentials are disabled. CORS is a browser
policy, not authentication: bind locally. Public hosting needs separately reviewed
TLS, authentication, rate limits, proxy logging, and deployment configuration.

```sh
python -m pytest -q
python -m ruff check .
python -m ruff check src/freightguard/api tests/test_api.py
```

Tests use synthetic requests and a stub, covering startup-only loading, contract
mismatches, missing files, trust/checksum configuration, loader errors, validation,
privacy-safe errors/logs, CORS, body limits, and OpenAPI. Existing artifact tests
verify real checksum enforcement. A manual real-artifact smoke check uses only the
synthetic example above, never test-set evaluation. Full Ruff retains the existing
inspection-script import issue, which must be preserved.


## Milestone 7 hardening

Startup now rejects malformed/truncated category vocabulary contracts before
marking the model ready. Unexpected sanitized 500 responses preserve the explicit
allowed-origin policy, so browsers receive a useful API error. All responses carry
nosniff, no-referrer and no-store headers. A new integration regression proves
checksum failure prevents deserialization. No endpoint, threshold or artifact
changed. Native startup remains local-only; container candidates and pending
verification are documented in DEPLOYMENT.md. See SECURITY.md for audit scope.
