"""Tests for aisc_plugin_llm_eval.model_provider.FilePredictionsProvider."""

import json

import yaml

from aisc_plugin_llm_eval.model_provider import FilePredictionsProvider


class TestFilePredictionsProvider:
    """FilePredictionsProvider parses YAML/JSON bytes into Python objects."""

    def test_parses_json_bytes(self):
        data = [
            {"prompt": "What is 1+1?", "response": "2", "answer": "2"},
            {
                "prompt": "Capital of Luxembourg?",
                "response": "Luxembourg",
                "answer": "Luxembourg",
            },
        ]
        raw = json.dumps(data).encode("utf-8")
        provider = FilePredictionsProvider(raw)
        assert provider._data == data

    def test_parses_yaml_bytes(self):
        data = [
            {"predictions": [{"score": 0.9}]},
        ]
        raw = yaml.dump(data).encode("utf-8")
        provider = FilePredictionsProvider(raw)
        assert provider._data == data

    def test_get_data_returns_parsed(self):
        data = [
            {"a": 1},
        ]
        raw = json.dumps(data).encode("utf-8")
        provider = FilePredictionsProvider(raw)
        assert provider.get_data() == data

    def test_empty_list(self):
        raw = json.dumps([]).encode("utf-8")
        provider = FilePredictionsProvider(raw)
        assert provider._data == []

    def test_nested_structure(self):
        data = [
            {
                "outputs": [
                    {"row_index": 0, "response": "hello", "metrics": {"bleu": 0.8}}
                ]
            },
        ]
        raw = json.dumps(data).encode("utf-8")
        provider = FilePredictionsProvider(raw)
        assert provider._data[0]["outputs"][0]["metrics"]["bleu"] == 0.8
