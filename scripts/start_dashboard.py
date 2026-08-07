"""Start the Phase 4 Streamlit dashboard."""

from pathlib import Path

from streamlit.web import cli as stcli

if __name__ == "__main__":
    dashboard = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"
    stcli.main_run([str(dashboard)])
