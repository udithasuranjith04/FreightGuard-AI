# Portfolio release review checklist

The final audit accepted the native/local educational application and the user
authorized its Milestone 7 source checkpoint. See FINAL_AUDIT.md for executed
checks. A tag, push or external deployment is not authorized. The open checks
below remain gates for broader distribution/container/hosting targets.

## Verified locally

- [x] Milestone 6 reviewed, clean-installed, checked and committed as d9cdf73.
- [x] Both inspection-script states and frozen model/test artifacts preserved.
- [x] Strict five-input requests, trusted startup-only loading and checksum rejection.
- [x] Historical metrics distinguished from actual health/model status.
- [x] Backend and frontend synthetic test suites, type checks, lint/build.
- [x] Real synthetic prediction through browser to FastAPI at frozen 0.40.
- [x] No model training, private-data changes or held-out test reevaluation.
- [x] Dependency advisory checks and redacted Git/public-file/bundle scan.
- [x] Local setup, configuration, security scope and limitations documented.

## Final human/source release gates

- [x] Review all Milestone 7 diffs, test evidence and remaining warnings.
- [x] Review index separately: inspect_data.py still contains the user's empty staged blob.
- [x] Confirm only intended source/config/docs are selected for the checkpoint; no force-add or blanket commit.
- [x] Correct author/committer metadata on only the nine unpublished commits; verify their trees and preserve the published base.
- [x] Add a scoped MIT license for original application source code only; exclude data, model artifacts and separately licensed dependencies.
- [ ] Review the two already-published commits' machine-local author metadata before making the repository public; they were not rewritten.
- [ ] Confirm dataset provenance/license and artifact sharing rights before distributing either.
- [x] Keep dataset provenance uncertainty explicit and keep the dataset and model artifacts out of Git and out of the source-license grant.
- [ ] Review synthetic screenshots before adding public screenshots; generated results stay ignored.
- [ ] Run prepared GitHub Actions on the intended repository; no remote CI run verified here.
- [ ] Pin/review third-party action commits and base-image digests for a release gate.
- [ ] Verify fresh Linux Python install against pins; preserve original artifact compatibility.
- [ ] On a Docker-capable host, validate Compose, build, start, test trust/missing/hash errors,
      verify security headers/read-only operation, and scan images.
- [ ] Manually review screen-reader behavior and browsers beyond Chromium.
- [x] User authorizes the explicit-path M7 source commit after passing checks.
- [ ] Separately approve any release tag, push or external deployment.

## Additional gates before external hosting

- [ ] Explicit user approval for hosting/provider/audience.
- [ ] Reviewed TLS, authentication, allowed origins, resource/rate limits and proxy trust.
- [ ] Reviewed operational logging, monitoring, incident response and rollback.
- [ ] Independently trusted artifact provisioning; never model uploads/downloads on request.
- [ ] Preserve educational labels and all-late/weak within-mode findings everywhere.

## ML gate

V1 is not approved for operational alerts. The final cutoff classified every test
order late; supported within-mode ranking is near chance. A model redesign and
fresh prospective evaluation need separate authorization. Do not reuse the old
holdout or change the threshold during release work.

Suggested final source checkpoint after review:
`chore: prepare educational portfolio release and integration QA`.
Use an explicit-path commit, excluding inspect_data.py and all ignored outputs.
