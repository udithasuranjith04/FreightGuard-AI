# Deployment readiness: local educational release candidate

Nothing has been deployed externally. This milestone prepares reviewable local
configuration, not a production deployment or validated model. Native local
Python/Vite startup is tested; see README.md and FRONTEND.md.

## Configuration

| Setting | Meaning | Default |
| --- | --- | --- |
| FREIGHTGUARD_MODEL_PATH | Trusted local pipeline location, backend only | Repository-relative native default; /models/pipeline.joblib in container |
| FREIGHTGUARD_TRUST_LOCAL_MODEL | Explicit opt-in to deserialize | false |
| FREIGHTGUARD_MODEL_SHA256 | Independently checked lowercase artifact identity | empty, predictions unavailable |
| FREIGHTGUARD_CORS_ORIGINS | Comma-separated explicit browser origins | Two localhost dev origins natively; explicitly set in Compose |
| VITE_API_BASE_URL | Public URL used by the browser, compiled at build time | http://127.0.0.1:8000 |

Never put credentials or model-trust controls in VITE variables. Bad browser API
configuration now produces a safe status error rather than crashing the dashboard.
Changing a frontend build argument needs a rebuild. Docker service name `backend`
is not a browser-resolvable API base URL; local browser requests use loopback.

The sample Nginx CSP permits only loopback API destinations. Any reviewed change
to the public API URL must also update `connect-src`, backend allowed origins,
TLS and hosting settings. CORS is not authentication. Native access logs and
container access logs are disabled; do not introduce request-payload logging.

## Optional containers (prepared, not runtime verified)

Docker/Compose is not installed in this audit environment. YAML parsing passed;
`docker compose config`, image builds, Nginx startup and image scans cannot be
claimed as passed. Run these on a Docker-capable machine before release:

```sh
docker compose config
docker compose build
docker compose up
```

Base Compose starts without a model mount: `/health` works, `/model/info` reports
unavailable, prediction returns 503. Both host ports bind only to 127.0.0.1:
frontend 5173, backend 8000. Container internal bind 0.0.0.0 does not mean the
sample configuration is intended for public exposure.

For the existing original local artifact, review/trust it and verify its hash,
then use the explicit read-only mount override:

```sh
shasum -a 256 data/processed/models/v1/pipeline.joblib
export FREIGHTGUARD_TRUST_LOCAL_MODEL=true
export FREIGHTGUARD_MODEL_SHA256=e3d46fa78998d13584ed7d7ea88bd321c69e2773aa9b6f18eab20eee73d0ddef
docker compose -f compose.yaml -f compose.model.yaml config
docker compose -f compose.yaml -f compose.model.yaml up --build
```

The opt-in override fails if the host artifact is missing, rather than creating a
misleading directory in its place. Base Compose is the no-artifact startup route.
The model is never copied into a build context/image. Its host file must be
readable by container UID 10001. Do not change the source artifact or loosen
permissions on private directories merely to satisfy a container error.

The backend image installs exact runtime pins and runs as UID 10001. The frontend
uses a multistage Node build plus unprivileged Nginx. Compose drops capabilities,
sets no-new-privileges, and uses read-only roots with bounded /tmp mounts.
The backend healthcheck measures liveness only; check model_ready separately.
No restart policy hides a failing candidate during review.

`.dockerignore` allowlists source/config/docs only. It excludes .git, raw/processed
data, local environments, secrets, node_modules, build output and browser results.
No credentials are supplied as build arguments. Base image tags are not digest
pinned; resolve/record reviewed digests and scan images before publishing.
Nginx adds framing/MIME/referrer/permissions/CSP headers and disables access logs.
These are defense-in-depth candidates, not proof of a hardened deployment.

Stop the Compose application with Ctrl+C, then `docker compose down`. No volumes
hold customer data or generated models. Model loading happens once per worker;
after trust/hash/path changes restart the backend. There is no artifact hot reload.

## Reproducibility and CI

`requirements/runtime.txt` and `requirements/dev.txt` record the exact Python 3.12
versions in the working environment. They include transitive packages observed on
this platform. They are not hash-locked or a verified Linux dependency lock. A
fresh Linux/container install remains a release check. Preserve scikit-learn's
artifact-version match; never refit the frozen artifact to repair installation.
`npm ci` is verified with the frontend package lock.

`.github/workflows/checks.yml` prepares synthetic backend checks, frontend
checks/build/audit and redacted repository scans. It needs no private dataset,
artifact or secret. CI has read-only permissions and no deployment job. It
explicitly excludes the preserved user inspection script from Ruff. A full local
Ruff run is still reported separately. Actions use version tags, not immutable
commit pins; review/pin actions before relying on it as a release gate. No workflow
has been pushed/executed by this milestone. Browser integration still requires
the separately trusted local model and both local servers.

## Release and operational gates

See RELEASE_CHECKLIST.md. Before public release: review the final diff and index,
run CI on the intended repository, verify container builds/startup/error modes,
scan images, record dependency/base-image identities, and confirm any data or
artifact distribution rights. The root MIT license covers only original
application source code; it does not license dataset contents, serialized model
artifacts, third-party materials or dependencies. Dataset provenance and terms
remain unverified, so keep the dataset and artifacts excluded. Before public hosting: approve
infrastructure and audience; add TLS, authentication, rate/resource limits,
monitoring and a reviewed logging policy. Operational alerts require a separate
problem/data redesign and prospective evaluation. No existing model metric earns
production approval, and this milestone authorizes no new test evaluation.

Container choices follow the [Docker Compose service reference](https://docs.docker.com/reference/compose-file/services/)
and [unprivileged Nginx documentation](https://github.com/nginx/docker-nginx-unprivileged).
