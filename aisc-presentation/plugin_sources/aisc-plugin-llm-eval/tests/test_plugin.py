"""Tests for aisc_plugin_llm_eval.plugin.LLMEvaluationPlugin.

All HuggingFace model interactions are mocked — no real models are loaded.
"""

from unittest.mock import MagicMock, patch

import pytest
import pandas as pd

from aisc_plugin_interface import Measure, ChartType

from aisc_plugin_llm_eval import LLMEvaluationPlugin
from aisc_plugin_llm_eval.dataset_provider import DataFrameProvider
from aisc_plugin_llm_eval.model_provider import FilePredictionsProvider

from tests.conftest import FakeLLMOutput

PATCH_LLM_WRAPPER = "llm_eval_framework.llm.LLMGenerationWrapper"
PATCH_COMPUTE_METRICS = "llm_eval_framework.evaluation.compute_metrics_in_batches"


def _make_plugin(*, dataset_bytes: bytes | None = None) -> LLMEvaluationPlugin:
    """Instantiate a plugin, optionally with a dataset already loaded."""
    plugin = LLMEvaluationPlugin()
    if dataset_bytes is not None:
        plugin.set_input_content("dataset", dataset_bytes)
    return plugin


def _single_prompt_config(**overrides) -> dict:
    """Config dict for single-prompt mode (prompt is set)."""
    data = {
        "model_name": "test-model/tiny",
        "batch_size": 1,
        "temperature": 0.6,
        "max_new_tokens": 64,
        "prompt": "Capital of Luxembourg?",
        "answer": "Luxembourg",
    }
    data.update(overrides)
    return data


def _dataset_config(**overrides) -> dict:
    """Config dict for dataset mode (prompt is empty)."""
    data = {
        "model_name": "test-model/tiny",
        "batch_size": 2,
        "temperature": 0.6,
        "max_new_tokens": 64,
        "prompt": "",
        "answer": "",
    }
    data.update(overrides)
    return data


class TestPluginClassAttributes:
    """Plugin-level class attributes and classmethods."""

    def test_metric_names_combines_heuristic_and_judge(self):
        names = LLMEvaluationPlugin.metric_names()
        assert "bleu" in names
        assert "rouge" in names
        assert "factual_accuracy" in names
        assert "safety" in names

    def test_metric_names_count(self):
        names = LLMEvaluationPlugin.metric_names()
        expected = len(LLMEvaluationPlugin.metric_heuristic_names) + len(
            LLMEvaluationPlugin.metric_judge_names
        )
        assert len(names) == expected

    def test_display_icon(self):
        plugin = _make_plugin()
        assert plugin.display_icon == "grading"


class TestInputProviders:
    """set_dataset_input_provider and set_model_input_provider."""

    def test_set_dataset_input_provider(self, dataset_bytes):
        plugin = _make_plugin()
        plugin.set_input_content("dataset", dataset_bytes)
        provider = plugin._input_provider_instances.get("dataset")
        assert isinstance(provider, DataFrameProvider)
        assert isinstance(plugin.get_input_data("dataset"), pd.DataFrame)

    def test_set_model_input_provider(self):
        import json

        data = [{"prompt": "q", "response": "a", "answer": "a"}]
        raw = json.dumps(data).encode()
        plugin = _make_plugin()
        plugin.set_input_content("llm-predictions", raw)
        provider = plugin._input_provider_instances.get("llm-predictions")
        assert isinstance(provider, FilePredictionsProvider)
        assert provider.get_data() == data


class TestComputeOutputsSinglePrompt:
    """Single-prompt mode: config.prompt is set, no dataset needed."""

    def test_returns_one_output(self):
        wrapper_inst = MagicMock()
        wrapper_inst.generate.return_value = [FakeLLMOutput(content="Luxembourg")]
        wrapper_inst.unload = MagicMock()

        plugin = _make_plugin()
        config = plugin.validate_config_form_data(_single_prompt_config())

        with patch(PATCH_LLM_WRAPPER, return_value=wrapper_inst):
            outputs = plugin.compute_outputs(config)

        assert len(outputs) == 1
        assert outputs[0]["response"] == "Luxembourg"
        assert outputs[0]["prompt"] == "Capital of Luxembourg?"
        assert outputs[0]["answer"] == "Luxembourg"

    def test_unloads_wrapper_after_generation(self):
        wrapper_inst = MagicMock()
        wrapper_inst.generate.return_value = [FakeLLMOutput(content="x")]

        plugin = _make_plugin()
        config = plugin.validate_config_form_data(_single_prompt_config())

        with patch(PATCH_LLM_WRAPPER, return_value=wrapper_inst):
            plugin.compute_outputs(config)

        wrapper_inst.unload.assert_called_once()


class TestComputeOutputsDataset:
    """Dataset mode: config.prompt is empty, dataset provider is used."""

    def test_outputs_match_dataset_length(self, sample_rows, dataset_bytes):
        wrapper_inst = MagicMock()
        wrapper_inst.generate.side_effect = lambda ps: [
            FakeLLMOutput(content=f"resp_{i}") for i in range(len(ps))
        ]
        wrapper_inst.unload = MagicMock()

        plugin = _make_plugin(dataset_bytes=dataset_bytes)
        config = plugin.validate_config_form_data(_dataset_config())

        with patch(PATCH_LLM_WRAPPER, return_value=wrapper_inst):
            outputs = plugin.compute_outputs(config)

        assert len(outputs) == len(sample_rows)

    def test_output_contains_expected_keys(self, sample_rows, dataset_bytes):
        wrapper_inst = MagicMock()
        wrapper_inst.generate.side_effect = lambda ps: [
            FakeLLMOutput(content="r") for _ in ps
        ]
        wrapper_inst.unload = MagicMock()

        plugin = _make_plugin(dataset_bytes=dataset_bytes)
        config = plugin.validate_config_form_data(_dataset_config())

        with patch(PATCH_LLM_WRAPPER, return_value=wrapper_inst):
            outputs = plugin.compute_outputs(config)

        for output in outputs:
            assert "row_index" in output
            assert "prompt" in output
            assert "answer" in output
            assert "response" in output

    def test_raises_when_no_dataset_and_empty_prompt(self):
        plugin = _make_plugin()  # no dataset
        config = plugin.validate_config_form_data(_dataset_config())

        with pytest.raises(Exception, match="Dataset input provider not set"):
            with patch(PATCH_LLM_WRAPPER):
                plugin.compute_outputs(config)


class TestComputeHeuristicMetrics:
    """_compute_heuristic_metrics scores outputs with all heuristic metrics."""

    def test_returns_scores_per_output(self, mock_compute_metrics):
        plugin = _make_plugin()
        outputs = [{"prompt": "q", "response": "a", "answer": "a"}] * 2

        scores = {name: 0.5 for name in plugin.metric_heuristic_names}
        with mock_compute_metrics(scores):
            result = plugin._compute_heuristic_metrics(outputs)

        assert len(result) == 2
        for row in result:
            for name in plugin.metric_heuristic_names:
                assert name in row
                assert row[name] == 0.5

    def test_handles_metric_failure_gracefully(self):
        """When compute_metrics_in_batches raises, the metric gets None scores."""
        plugin = _make_plugin()
        outputs = [{"prompt": "q", "response": "a", "answer": "a"}]

        def _failing_compute(outputs, retries, batch_size, metric_name, **kwargs):
            if metric_name == "bleu":
                raise RuntimeError("bleu broke")
            return [{"score": 0.9} for _ in outputs]

        with patch(PATCH_COMPUTE_METRICS, side_effect=_failing_compute):
            result = plugin._compute_heuristic_metrics(outputs)

        assert result[0]["bleu"] is None
        assert result[0]["rouge"] == 0.9


class TestEvaluate:
    """Full evaluate() pipeline: compute_outputs + heuristic metrics."""

    def test_evaluate_single_prompt_heuristic_only(self, mock_compute_metrics):
        """Evaluate with a single prompt, no judge model."""
        wrapper_inst = MagicMock()
        wrapper_inst.generate.return_value = [FakeLLMOutput(content="Luxembourg")]
        wrapper_inst.unload = MagicMock()

        plugin = _make_plugin()
        config_data = _single_prompt_config()

        scores = {name: 0.7 for name in plugin.metric_heuristic_names}
        with (
            mock_compute_metrics(scores),
            patch(PATCH_LLM_WRAPPER, return_value=wrapper_inst),
        ):
            results = plugin.evaluate(config_data)

        assert len(results) == 1
        assert results[0]["response"] == "Luxembourg"
        for name in plugin.metric_heuristic_names:
            assert name in results[0]

    def test_evaluate_with_precomputed_model_predictions(self, mock_compute_metrics):
        """When model_input_provider is set, skip compute_outputs."""
        import json

        predictions = [
            {
                "prompt": "Capital of Luxembourg?",
                "response": "Luxembourg",
                "answer": "Luxembourg",
            }
        ]
        plugin = _make_plugin()
        plugin.set_input_content("llm-predictions", json.dumps(predictions).encode())

        config_data = _single_prompt_config()
        scores = {name: 0.5 for name in plugin.metric_heuristic_names}
        with mock_compute_metrics(scores), patch(PATCH_LLM_WRAPPER) as MockWrapper:
            results = plugin.evaluate(config_data)

        MockWrapper.assert_not_called()
        assert len(results) == 1
        assert results[0]["response"] == "Luxembourg"


class TestExportMetrics:
    """export_metric_* methods generated by @add_metrics."""

    def test_all_export_methods_exist(self):
        plugin = _make_plugin()
        for name in LLMEvaluationPlugin.metric_names():
            method_name = f"export_metric_{name}"
            assert hasattr(plugin, method_name), f"Missing {method_name}"

    def test_export_metric_returns_measures(self):
        plugin = _make_plugin()
        evaluation_output = [{"bleu": 0.8, "rouge": 0.7}]
        measures = plugin.export_metric_bleu(  # ty: ignore[unresolved-attribute]
            evaluation_output
        )
        assert len(measures) == 1
        assert isinstance(measures[0], Measure)
        assert measures[0].name == "bleu"
        assert measures[0].score == 0.8

    def test_export_metrics_aggregation(self):
        """export_metrics() on the base class aggregates all @metric methods."""
        plugin = _make_plugin()
        output = {name: 0.5 for name in LLMEvaluationPlugin.metric_names()}
        all_measures = plugin.export_metrics([output])
        assert len(all_measures) == len(LLMEvaluationPlugin.metric_names())


class TestGetMetricVisualizations:
    """get_metric_visualizations returns correct chart types per mode."""

    def test_single_prompt_no_judge(self):
        """Single prompt, no judge => TABLE + RADAR(heuristic)."""
        config_data = _single_prompt_config()
        plugin = _make_plugin()
        vizs = plugin.get_metric_visualizations(config_data)

        assert vizs[0].chart_type == ChartType.TABLE
        assert vizs[1].chart_type == ChartType.RADAR
        assert vizs[1].metrics == LLMEvaluationPlugin.metric_heuristic_names

    def test_single_prompt_with_judge(self):
        """Single prompt with judge => TABLE + RADAR(heuristic) + RADAR(judge)."""
        config_data = _single_prompt_config(model_judge_name="judge/model")
        plugin = _make_plugin()
        vizs = plugin.get_metric_visualizations(config_data)

        assert vizs[0].chart_type == ChartType.TABLE
        assert vizs[1].chart_type == ChartType.RADAR
        assert vizs[2].chart_type == ChartType.RADAR
        assert vizs[2].metrics == LLMEvaluationPlugin.metric_judge_names

    def test_dataset_mode_no_judge(self):
        """Dataset mode (empty prompt) => TABLE + SCATTER(heuristic) + KDE per metric."""
        config_data = _dataset_config()
        plugin = _make_plugin()
        vizs = plugin.get_metric_visualizations(config_data)

        assert vizs[0].chart_type == ChartType.TABLE
        assert vizs[1].chart_type == ChartType.SCATTER
        kde_vizs = [v for v in vizs if v.chart_type == ChartType.KDE]
        assert len(kde_vizs) == len(LLMEvaluationPlugin.metric_heuristic_names)

    def test_dataset_mode_with_judge(self):
        """Dataset mode with judge => TABLE + SCATTER(h) + SCATTER(j) + KDE per all."""
        config_data = _dataset_config(model_judge_name="judge/model")
        plugin = _make_plugin()
        vizs = plugin.get_metric_visualizations(config_data)

        scatter_vizs = [v for v in vizs if v.chart_type == ChartType.SCATTER]
        assert len(scatter_vizs) == 2

        kde_vizs = [v for v in vizs if v.chart_type == ChartType.KDE]
        assert len(kde_vizs) == len(LLMEvaluationPlugin.metric_names())
