import io

import pandas as pd
from aisc_plugin_interface import BaseInputProvider

from .utils import get_items


class DataFrameProvider(BaseInputProvider):
    def _read_data(self, file_content: bytes) -> pd.DataFrame:
        import pandas as pd

        file_stream = io.BytesIO(file_content)
        try:
            return pd.read_parquet(file_stream)
        except Exception:
            file_stream.seek(0)
            try:
                return pd.read_csv(file_stream)
            except Exception as e:
                raise ValueError("File is neither a valid Parquet nor CSV.") from e


class LLMDataset:
    def __init__(self, dataframe: pd.DataFrame, prompt_template: str):
        from llm_eval_framework.prompt import Prompt
        from llm_eval_framework.dataset import Dataset, DatasetMetadata

        prompt = Prompt(template=prompt_template)
        # NOTE: adding the empty metadata for compatability with llm_eval_framework
        empty_metadata = DatasetMetadata(name="", description="", task="")

        self.dataset = Dataset(
            data=dataframe, metadata=empty_metadata, prompt_template=prompt
        )

    def __getitem__(self, idx: int) -> tuple:
        _dataset = self.dataset
        row = _dataset.data.iloc[idx].to_dict()
        prompt = _dataset.prompts[idx]

        if _dataset.answers is None:
            answer = None
        else:
            answer = _dataset.answers[idx]

        return (idx, row, prompt, answer)

    def iter(self, batch_size: int):
        for start in range(0, len(self), batch_size):
            end = min(start + batch_size, len(self))
            yield get_items(
                self,  # ty: ignore[invalid-argument-type]
                *range(start, end),
                batch=True,
            )

    def __len__(self) -> int:
        return len(self.dataset.data)
