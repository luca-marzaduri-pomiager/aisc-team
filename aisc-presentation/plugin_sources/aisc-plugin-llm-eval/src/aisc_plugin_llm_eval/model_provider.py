import io
import json
import yaml
import pandas as pd
from typing import Any

from aisc_plugin_interface import BaseInputProvider


class FilePredictionsProvider(BaseInputProvider):
    def _read_data(self, file_content: bytes) -> Any:
        # Try JSON
        try:
            data = json.loads(file_content.decode("utf-8"))
            if isinstance(data, dict):
                return [data]
            if isinstance(data, list):
                return data
        except Exception:
            pass

        # Try YAML
        try:
            data = yaml.safe_load(file_content.decode("utf-8"))
            if isinstance(data, dict):
                return [data]
            if isinstance(data, list):
                return data
        except Exception:
            pass

        # Try CSV
        file_stream = io.BytesIO(file_content)
        try:
            df = pd.read_csv(file_stream)
            return df.to_dict(orient="records")
        except Exception:
            pass

        # Try Parquet
        file_stream.seek(0)
        try:
            df = pd.read_parquet(file_stream)
            return df.to_dict(orient="records")
        except Exception:
            pass

        raise ValueError("File is neither valid JSON, YAML, CSV, nor Parquet.")
