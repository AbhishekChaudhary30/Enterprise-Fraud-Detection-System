# Example API Requests

```powershell
$login = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/login -Body @{ username = 'admin'; password = $env:ADMIN_PASSWORD }
$headers = @{ Authorization = "Bearer $($login.access_token)" }
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/models/latest -Headers $headers
```

For a real transaction, send all feature columns expected by the saved pipeline:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/predict -Headers $headers -ContentType 'application/json' -Body '{"features":{"Time":0,"Amount":100.0,"V1":0.0},"threshold":0.32}'
```
