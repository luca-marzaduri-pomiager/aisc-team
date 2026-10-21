# aisc-plugin-llm-eval

[![CI](https://github.com/lux-ai-factory/aisc-plugin-llm-eval/actions/workflows/ci.yml/badge.svg)](https://github.com/lux-ai-factory/aisc-plugin-llm-eval/actions/workflows/ci.yml)

A Python plugin for LLM evaluation, implementing heuristic and LLM-as-a-judge metrics on HuggingFace models. Built on the [aisc-plugin-interface](https://github.com/lux-ai-factory/aisc-plugin-interface) framework and the [llm_eval_framework](https://github.com/serval-uni-lu/llm_eval) package.

## Features

- **Heuristic metrics**: Contains, Equals, Is JSON, Regex Match, Levenshtein, BLEU, ROUGE, Sentiment, ANLS
- **LLM-as-a-judge metrics**: Factual Accuracy, Answer Correctness, Bias, Safety, Instruction Following
- **Two evaluation modes**: Dataset mode (batch evaluation from a CSV or Parquet file) or single-prompt mode
- **Remote inference**: Optional server for offloading LLM inference to a GPU machine
- **Configurable generation**: Temperature, top-p, max tokens, batch size

## Installation

```bash
uv sync
```

## Quick Start

### Dataset Mode

Evaluate a model on a dataset provided as a CSV or Parquet file. The `prompt_template` field in the config uses placeholders to generate prompts from each row:

```python
from aisc_plugin_llm_eval import LLMEvaluationPlugin

plugin = LLMEvaluationPlugin()
plugin.set_input_content("dataset", csv_or_parquet_bytes)

results = plugin.evaluate({
    "prompt_template": "Question: {{question}}\nAnswer:",
    "model_name": "ibm-granite/granite-4.0-h-350m",
    "batch_size": 4,
    "temperature": 0.6,
    "max_new_tokens": 512,
})
```

### Prompt Mode

Evaluate a model on a single prompt (and optionally the expected answer):

```python
results = plugin.evaluate({
    "prompt_template": "Question: {{question}}\nAnswer:",
    "model_name": "ibm-granite/granite-4.0-h-350m",
    "prompt": "What is the capital of Luxembourg?",
    "answer": "Luxembourg",
    "temperature": 0.6,
    "max_new_tokens": 512,
})
```

### LLM-as-a-Judge

Add a judge model to compute judge metrics alongside heuristic metrics:

```python
results = plugin.evaluate({
    "prompt_template": "Question: {{question}}\nAnswer:",
    "model_name": "ibm-granite/granite-4.0-h-350m",
    "prompt": "What is the capital of Luxembourg?",
    "answer": "Luxembourg",
    "model_judge_name": "LiquidAI/LFM2.5-1.2B-Thinking",
    "batch_size_judge": 1,
    "retries_judge": 3,
})
```

## Metrics

### Heuristic Metrics

| Metric | Description |
|--------|-------------|
| Contains | Whether the response contains the expected answer |
| Equals | Whether the response exactly matches the expected answer |
| Is JSON | Whether the response is valid JSON |
| Regex Match | Whether the response matches a regex pattern |
| Levenshtein | Edit distance between response and expected answer |
| BLEU | Bilingual Evaluation Understudy score |
| ROUGE | Recall-Oriented Understudy for Gisting Evaluation |
| Sentiment | Sentiment analysis score |
| ANLS | Average Normalized Levenshtein Similarity |

### LLM-as-a-Judge Metrics

| Metric | Description |
|--------|-------------|
| Factual Accuracy | Whether the response is factually correct |
| Answer Correctness | Whether the response correctly answers the question |
| Bias | Whether the response contains biased content |
| Safety | Whether the response is safe and appropriate |
| Instruction Following | Whether the response follows the given instructions |

## Remote Inference

Due to the size of evaluated models, inference can be offloaded to a remote machine using the bundled [llm-server](./scripts/llm-server):

```bash
cd scripts/llm-server && uv sync
uv run uvicorn src.llm_server.__main__:app --host 0.0.0.0 --port 9008
```

Then configure the plugin to use the remote endpoint:

```python
results = plugin.evaluate({
    "prompt_template": "Question: {{question}}\nAnswer:",
    "model_name": "ibm-granite/granite-4.0-h-350m",
    "endpoint": "http://host.docker.internal:9008/generate",
    "prompt": "What is the capital of Luxembourg?",
})
```

## Development

### Setup

```bash
# Install dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install
```

### Commands

```bash
# Run tests
uv run pytest

# Run a single test
uv run pytest tests/test_utils.py::TestGetItemsSingleMode::test_single_index

# Linting
uv run ruff check src/

# Linting with auto-fix
uv run ruff check --fix src/

# Type checking
uv run ty check src/

# Format code
uv run ruff format src/

# Run all pre-commit hooks manually
uv run pre-commit run --all-files
```

### Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to run checks before each commit:

- **Ruff** - Linting and formatting
- **ty** - Type checking

Hooks are installed automatically when you run `uv run pre-commit install`. To skip hooks temporarily:

```bash
git commit --no-verify -m "message"
```

### Project Structure

```
src/aisc_plugin_llm_eval/
├── __init__.py              # Public exports (LLMEvaluationPlugin)
├── plugin.py                # Main plugin class, orchestrates evaluation
├── form_schema.py           # Pydantic config schema (form fields)
├── dataset_provider.py      # DataFrameProvider for CSV/Parquet files
├── model_provider.py        # Pre-computed LLM predictions (JSON, YAML, CSV, Parquet)
└── utils.py                 # add_metrics decorator, get_items helper

scripts/llm-server/          # Optional remote inference server
└── src/llm_server/
    ├── __main__.py           # FastAPI app with /generate endpoint
    └── llm.py                # HuggingFace LLM wrapper
```

## Tech Stack

- **Python** 3.12+
- **Pydantic** - Configuration and validation
- **pandas** - Data processing
- **llm_eval_framework** - Metric computation and LLM generation
- **uv** - Package management
- **Ruff** - Linting and formatting
- **ty** - Type checking

## Plugin Metadata

| Field | Value |
|-------|-------|
| Name | LLM Evaluation Plugin |
| Description | A Python plugin for LLM evaluation, implementing heuristic metrics (Contains, Equals, Is JSON, Regex Match, Levenshtein, BLEU, ROUGE, Sentiment, ANLS) and LLM-as-a-judge metrics (Factual Accuracy, Answer Correctness, Bias, Safety, Instruction Following). Supports dataset and single-prompt evaluation modes with optional remote inference. |
| License | - |
| Verification type | Technical test |
| Project | [aisc-plugin-llm-eval](https://github.com/lux-ai-factory/aisc-plugin-llm-eval) |
| Branch | main |
| Version | 0.2.2 |
| Project maturity | In development |
| Scientific reference | - |
| Verification targets | [LLM Evaluation] [Heuristic Metrics] [LLM-as-a-Judge] [Text Generation] |
| Sector | [AI/ML] [NLP] [LLM] |
