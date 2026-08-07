"""Streamlit dashboard for the Enterprise Fraud Detection System."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(page_title="Enterprise Fraud Detection", page_icon="shield", layout="wide")


def api_call(base_url: str, token: str, method: str, path: str, **kwargs: Any) -> requests.Response:
    """Call an authenticated API route."""
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    return requests.request(method, f"{base_url}{path}", headers=headers, timeout=60, **kwargs)


st.title("Enterprise Fraud Detection")
st.caption("Authenticated model serving, evaluation, explanations, and prediction history")
base_url = st.sidebar.text_input("API URL", "http://127.0.0.1:8000/api/v1")
username = st.sidebar.text_input("Username", "admin")
password = st.sidebar.text_input("Password", type="password")

if "token" not in st.session_state:
    st.session_state.token = ""

if st.sidebar.button("Login", type="primary"):
    response = requests.post(
        f"{base_url}/login",
        data={"username": username, "password": password},
        timeout=30,
    )
    if response.ok:
        st.session_state.token = response.json()["access_token"]
        st.sidebar.success("Authenticated")
    else:
        st.sidebar.error(response.text)

if not st.session_state.token:
    st.info("Authenticate with the API to access prediction and model views.")
    st.stop()

token = st.session_state.token
health = requests.get(f"{base_url}/health", timeout=30)
models = api_call(base_url, token, "GET", "/models").json()
latest = api_call(base_url, token, "GET", "/models/latest").json()

metric_path = Path(__file__).resolve().parents[1] / "reports" / "evaluation" / "metrics.json"
metrics = json.loads(metric_path.read_text(encoding="utf-8")) if metric_path.exists() else {}

columns = st.columns(4)
columns[0].metric("Service", "Healthy" if health.ok else "Unavailable")
columns[1].metric("Latest model", models.get("latest", "unknown"))
columns[2].metric("Algorithm", latest.get("metadata", {}).get("selected_model", "unknown"))
columns[3].metric("PR AUC", f"{metrics.get('pr_auc', 0):.4f}")

prediction_tab, csv_tab, reports_tab, history_tab, admin_tab = st.tabs(
    ["Prediction", "CSV Upload", "Reports", "History", "Admin"]
)

with prediction_tab:
    st.subheader("Single prediction")
    feature_text = st.text_area(
        "Feature JSON",
        '{"Time": 0, "Amount": 100.0, "V1": 0.0}',
        height=140,
    )
    threshold = st.slider("Decision threshold", 0.01, 0.99, 0.32, 0.01)
    if st.button("Score transaction", type="primary"):
        try:
            payload = {"features": json.loads(feature_text), "threshold": threshold}
            response = api_call(base_url, token, "POST", "/predict", json=payload)
            if response.ok:
                result = response.json()
                result_columns = st.columns(3)
                result_columns[0].metric("Predicted label", result["predicted_label"])
                result_columns[1].metric("Fraud probability", f"{result['fraud_probability']:.4f}")
                result_columns[2].metric("Confidence", f"{result['confidence_score']:.4f}")
            else:
                st.error(response.text)
        except json.JSONDecodeError:
            st.error("Feature JSON is invalid")

with csv_tab:
    st.subheader("Batch CSV prediction")
    uploaded = st.file_uploader("Upload a feature CSV", type=["csv"])
    if uploaded is not None and st.button("Predict CSV", type="primary"):
        response = api_call(
            base_url,
            token,
            "POST",
            "/upload",
            files={"file": (uploaded.name, uploaded.getvalue(), "text/csv")},
        )
        if response.ok:
            st.download_button(
                "Download predictions", response.content, f"predictions_{uploaded.name}", "text/csv"
            )
            st.dataframe(
                pd.read_csv(__import__("io").BytesIO(response.content)), use_container_width=True
            )
        else:
            st.error(response.text)

with reports_tab:
    st.subheader("Evaluation and explainability")
    st.json(metrics)
    figure_directory = Path(__file__).resolve().parents[1] / "reports" / "figures" / "evaluation"
    available_figures = sorted(figure_directory.glob("*.png"))
    for figure in available_figures:
        st.image(str(figure), caption=figure.stem, use_container_width=True)
    shap_directory = Path(__file__).resolve().parents[1] / "reports" / "shap"
    for figure in sorted(shap_directory.glob("*.png")):
        st.image(str(figure), caption=f"SHAP: {figure.stem}", use_container_width=True)

with history_tab:
    st.subheader("Prediction history")
    response = api_call(base_url, token, "GET", "/history")
    if response.ok:
        history = response.json().get("history", [])
        st.dataframe(pd.DataFrame(history), use_container_width=True)
        if history:
            chart = pd.DataFrame(history)
            if "fraud_count" in chart:
                st.plotly_chart(
                    px.bar(chart, y="fraud_count", title="Fraud predictions by batch"),
                    use_container_width=True,
                )
    else:
        st.error(response.text)

with admin_tab:
    st.subheader("Model administration")
    st.json(models)
    if st.button("Reload latest model"):
        response = api_call(base_url, token, "POST", "/admin/reload")
        st.success(response.json() if response.ok else response.text)
