# Deployment Guide

## Container

Build the production image:

```powershell
docker build --target production -t enterprise-fraud-detection:1.0.0 .
```

Run with environment variables and mounted model/artifact directories:

```powershell
docker compose up --build -d
```

The Compose health check calls `/api/v1/health`. Keep `.env` outside source control and provide a strong `JWT_SECRET`.

## Operational Notes

- Pin the model version by controlling the mounted `models/` directory.
- Keep raw data, credentials, and generated prediction records out of image layers.
- Use a reverse proxy with TLS and a distributed rate limiter for multi-instance deployments.
- Phase 5 intentionally does not include cloud infrastructure or CI/CD deployment automation.
