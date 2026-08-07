"""Generate a valid sample feature CSV from the configured raw dataset."""

from enterprise_fraud_detection.config import get_settings
from enterprise_fraud_detection.data.dataset import DatasetManager

if __name__ == "__main__":
    settings = get_settings()
    frame = DatasetManager(settings).load().drop(columns=[settings.dataset.target_column]).head(5)
    output = settings.paths.external_data / "sample_transactions.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    print(output)
