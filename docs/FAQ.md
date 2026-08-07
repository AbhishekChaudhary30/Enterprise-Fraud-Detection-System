# FAQ

## Which model is served?

The latest numeric version under `models/` is loaded. Historical versions can be addressed explicitly through the model routes and prediction payload.

## Where is the threshold configured?

`serving.default_threshold` controls API defaults. Individual prediction requests may provide a validated threshold.

## Where are monitoring outputs?

Runtime metrics are persisted to `artifacts/metrics.json`; drift reports go to `reports/drift/`; benchmark reports go to `reports/benchmarks/`.

## Does Phase 5 deploy to the cloud?

No. Docker and Compose are included; cloud deployment and CI/CD deployment automation are intentionally outside this phase.
