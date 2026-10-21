"""Shared test fixtures.

Provides mock objects that simulate HuggingFace models and the llm_eval_framework
so tests never download real models or run GPU inference.
"""

import io
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

import pandas as pd
import pytest

from aisc_plugin_llm_eval.dataset_provider import LLMDataset


@dataclass
class FakeLLMOutput:
    """Fake LLM output (mirrors llm_eval_framework.llm.LLMOutput)"""

    content: str
    logprobs: dict[str, Any] | None = None


@pytest.fixture()
def sample_rows():
    """Minimal rows with a 'question' and 'answer' column."""
    return [
        {"question": "What is 1+1?", "answer": "2"},
        {"question": "Capital of Luxembourg?", "answer": "Luxembourg"},
        {"question": "Color of sky?", "answer": "Blue"},
    ]


@pytest.fixture()
def template():
    return "Question: {{question}}\nAnswer:"


@pytest.fixture()
def dataset(sample_rows):
    """A valid dataset pd.DataFrame"""
    return pd.DataFrame(sample_rows)


@pytest.fixture()
def dataset_bytes(dataset):
    """A valid dataset as bytes."""
    parquet_buf = io.BytesIO()
    dataset.to_parquet(parquet_buf, index=False)
    return parquet_buf.getvalue()


@pytest.fixture()
def llm_dataset(dataset, template):
    return LLMDataset(dataset, template)


@pytest.fixture()
def mock_llm_wrapper():
    """A mock LLMGenerationWrapper whose generate() returns FakeLLMOutput."""
    wrapper = MagicMock()

    def _generate(prompts):
        if isinstance(prompts, str):
            prompts = [prompts]
        return [FakeLLMOutput(content=f"answer_{i}") for i in range(len(prompts))]

    wrapper.generate = MagicMock(side_effect=_generate)
    wrapper.unload = MagicMock()
    return wrapper


@pytest.fixture()
def mock_compute_metrics():
    """Returns a helper that patches compute_metrics_in_batches.

    Usage in tests:
        def test_something(mock_compute_metrics):
            scores = {"bleu": 0.8, "rouge": 0.7}
            with mock_compute_metrics(scores):
                ...
    """
    from contextlib import contextmanager
    from unittest.mock import patch

    @contextmanager
    def _patcher(metric_scores: dict[str, float]):
        """metric_scores maps metric_name -> fixed score for every output."""

        def fake_compute(
            outputs,
            retries,
            batch_size,
            metric_name,
            return_all_scores=False,
            **kwargs,
        ):
            score = metric_scores.get(metric_name)
            return [{"score": score} for _ in outputs]

        with patch(
            "llm_eval_framework.evaluation.compute_metrics_in_batches",
            side_effect=fake_compute,
        ) as mock:
            # Make mock accessible if the test wants to inspect calls
            yield mock

    return _patcher


@pytest.fixture()
def default_config_data():
    """Minimal valid config data dict for ConfigFormSchema."""
    return {
        "model_name": "test-model/tiny",
        "batch_size": 1,
        "temperature": 0.6,
        "max_new_tokens": 64,
        "prompt": "What is 1+1?",
        "answer": "2",
    }
