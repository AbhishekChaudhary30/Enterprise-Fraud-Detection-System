"""Protected model and report artifact endpoints."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from enterprise_fraud_detection.api.dependencies import admin_user, current_user

router = APIRouter()


def _relative_files(directory: Any) -> list[str]:
    """List files below a configured directory using safe relative names."""
    if not directory.exists():
        return []
    return [str(path.relative_to(directory)) for path in directory.rglob("*") if path.is_file()]


@router.get("/models")
async def models(
    request: Request, user: Annotated[dict[str, str], Depends(current_user)]
) -> dict[str, Any]:
    """List available model versions."""
    loader = request.app.state.loader
    return {"versions": loader.versions(), "latest": loader.latest_version()}


@router.get("/models/latest")
async def latest_model(
    request: Request, user: Annotated[dict[str, str], Depends(current_user)]
) -> dict[str, Any]:
    """Return latest model metadata and artifact locations."""
    bundle = request.app.state.loader.load()
    return {"version": bundle.version, "metadata": bundle.metadata}


@router.get("/models/{version}")
async def model_version(
    version: str,
    request: Request,
    user: Annotated[dict[str, str], Depends(current_user)],
) -> dict[str, Any]:
    """Return metadata for a requested historical model version."""
    bundle = request.app.state.loader.load(version)
    return {"version": bundle.version, "metadata": bundle.metadata}


@router.get("/reports")
async def reports(
    request: Request, user: Annotated[dict[str, str], Depends(current_user)]
) -> dict[str, Any]:
    """List generated evaluation, SHAP, and report artifacts."""
    settings = request.app.state.settings
    return {
        "evaluation": _relative_files(settings.evaluation.output_directory),
        "figures": _relative_files(settings.evaluation.plots_directory),
        "shap": _relative_files(settings.evaluation.shap_directory),
    }


@router.get("/reports/{artifact_path:path}")
async def report_file(
    artifact_path: str,
    request: Request,
    user: Annotated[dict[str, str], Depends(current_user)],
) -> FileResponse:
    """Download a generated report or figure from configured report directories."""
    settings = request.app.state.settings
    candidates = [
        settings.evaluation.output_directory / artifact_path,
        settings.evaluation.plots_directory / artifact_path,
        settings.evaluation.shap_directory / artifact_path,
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
    raise HTTPException(status_code=404, detail="Report artifact not found")


@router.post("/admin/reload")
async def reload_latest(
    request: Request, user: Annotated[dict[str, str], Depends(admin_user)]
) -> dict[str, str]:
    """Reload the latest model bundle for administrative use."""
    bundle = request.app.state.predictions.reload()
    return {"status": "reloaded", "version": bundle.version}
