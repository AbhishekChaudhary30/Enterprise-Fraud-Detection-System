# API Documentation

Base URL: `http://127.0.0.1:8000/api/v1`

Swagger UI: `/docs`

## Authentication

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/login -H "Content-Type: application/x-www-form-urlencoded" -d "username=admin&password=..."
```

Use the returned bearer token for protected routes.

## Routes

- `GET /health`: service health and latest model.
- `POST /login`: issue JWT for configured admin.
- `POST /predict`: score one feature object.
- `POST /predict/batch`: score JSON records.
- `POST /upload`: upload a feature CSV and download predictions.
- `GET /models`: list versions.
- `GET /models/latest`: latest metadata.
- `GET /models/{version}`: historical metadata.
- `GET /reports`: list evaluation and SHAP artifacts.
- `GET /reports/{path}`: download a report artifact.
- `GET /history`: recent prediction records.
- `POST /admin/reload`: clear and reload the latest model.
- `GET /metrics`: process and API metrics.
