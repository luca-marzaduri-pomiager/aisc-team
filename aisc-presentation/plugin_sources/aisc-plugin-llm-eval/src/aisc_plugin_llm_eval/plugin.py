import math
from itertools import cycle
from typing import TypeVar

from aisc_plugin_interface import (
    BaseEvaluationPlugin,
    MetricVisualization,
    ChartType,
    InputType,
    evaluation_input,
)

from .utils import add_metrics
from .form_schema import ConfigFormSchema
from .dataset_provider import DataFrameProvider, LLMDataset
from .model_provider import FilePredictionsProvider

T = TypeVar("T")


@add_metrics
@evaluation_input(
    name="llm-predictions",
    label="Predictions of the Evaluated LLM, as a JSON file",
    input_provider_class=FilePredictionsProvider,
    input_type=InputType.DATASET,
    required=False,
)
@evaluation_input(
    name="dataset",
    label="Dataset",
    input_provider_class=DataFrameProvider,
    input_type=InputType.DATASET,
    required=False,
)
class LLMEvaluationPlugin(BaseEvaluationPlugin[ConfigFormSchema]):
    plugin_name = "LLM Evaluation"

    ui_icon = "grading"

    form_ui_schema = {
        "prompt_template": {"ui:widget": "textarea", "ui:options": {"rows": 10}},
        "prompt": {"ui:widget": "textarea", "ui:options": {"rows": 10}},
        "text": {"ui:widget": "textarea"},
        "batch_size": {"ui:widget": "updown"},
        "temperature": {"ui:widget": "updown"},
        "max_new_tokens": {"ui:widget": "updown"},
        "enable_top_p": {"ui:widget": "checkbox"},
        "top_p": {"ui:widget": "range"},
        "top_p_judge": {"ui:widget": "range"},
    }

    eval_llm_wrapper = None
    eval_llm_model_name = ""

    judge_llm_wrapper = None
    judge_llm_model_name = ""

    metric_heuristic_names = [
        "contains",
        "equals",
        "is_json",
        "regex_match",
        "levenshtein",
        "bleu",
        "rouge",
        "sentiment",
        "anls",
    ]

    metric_judge_names = [
        "factual_accuracy",
        "answer_correctness",
        "bias",
        "safety",
        "instruction_following",
    ]

    @classmethod
    def metric_names(cls):
        return cls.metric_heuristic_names + cls.metric_judge_names

    def _compute_heuristic_metrics(
        self,
        outputs: list[dict],
        regex_pattern: str | None = None,
    ) -> list[dict[str, float | None]]:
        from llm_eval_framework.evaluation import compute_metrics_in_batches

        self.logger.info(
            "Computing %d heuristic metrics on %d outputs",
            len(self.metric_heuristic_names),
            len(outputs),
        )

        batch_size = len(outputs)

        metrics: dict[str, list[float | None]] = {}

        for i, metric_name in self.progress_bar(
            self.metric_heuristic_names,
            start=1,
            with_index=True,
            desc="Heuristic metrics",
        ):
            metric_kwargs = (
                dict(pattern=regex_pattern)
                if metric_name == "regex_match" and regex_pattern is not None
                else dict()
            )
            try:
                scores = [
                    res.get("score", None)
                    for res in compute_metrics_in_batches(
                        outputs,
                        1,
                        batch_size,
                        metric_name,
                        llm_judge_generation_wrapper=None,
                        return_all_scores=True,
                        **metric_kwargs,
                    )
                ]
                metrics[metric_name] = scores
            except Exception:
                self.logger.warning(
                    "Failed to compute heuristic metric '%s', skipping", metric_name
                )
                metrics[metric_name] = [None] * len(outputs)

        return [dict(zip(metrics.keys(), values)) for values in zip(*metrics.values())]

    def _compute_judge_metrics(self, outputs, config: ConfigFormSchema):
        from llm_eval_framework.evaluation import compute_metrics_in_batches

        sampling_params = dict(
            topk_logprobs=10,
            temperature=config.temperature_judge,
            max_new_tokens=config.max_new_tokens_judge,
            top_p=config.top_p_judge if config.enable_top_p_judge else None,
        )

        if (
            self.judge_llm_wrapper is None
            or config.model_judge_name != self.judge_llm_model_name
        ):
            from llm_eval_framework.llm import LLMGenerationWrapper

            self.logger.info(
                "Loading judge LLM: %s (endpoint=%s)",
                config.model_judge_name,
                config.endpoint or "local",
            )
            try:
                self.judge_llm_model_name = config.model_judge_name
                self.judge_llm_wrapper = LLMGenerationWrapper(
                    model_name=config.model_judge_name,
                    load_in_4bit=False,
                    load_in_8bit=False,
                    sampling_params=sampling_params,
                    endpoint=config.endpoint,
                )
            except Exception:
                self.logger.exception(
                    "Failed to load judge LLM '%s'", config.model_judge_name
                )
                raise

        retries = config.retries_judge
        batch_size = config.batch_size_judge

        self.logger.info(
            "Computing %d judge metrics (retries=%d, batch_size=%d)",
            len(self.metric_judge_names),
            retries,
            batch_size,
        )

        metrics: dict[str, list[float | None]] = {}

        for i, metric_name in self.progress_bar(
            self.metric_judge_names,
            start=1,
            with_index=True,
            desc="LLM-as-judge metrics",
        ):
            try:
                scores = [
                    res.get("score", None)
                    for res in compute_metrics_in_batches(
                        outputs,
                        retries,
                        batch_size,
                        metric_name,
                        llm_judge_generation_wrapper=self.judge_llm_wrapper,
                        return_all_scores=True,
                    )
                ]
                metrics[metric_name] = scores
            except Exception:
                self.logger.warning(
                    "Failed to compute judge metric '%s', skipping", metric_name
                )
                metrics[metric_name] = [None] * len(outputs)

        return [dict(zip(metrics.keys(), values)) for values in zip(*metrics.values())]

    def compute_outputs(self, config: ConfigFormSchema):
        import pandas as pd

        sampling_params = dict(
            temperature=config.temperature,
            max_new_tokens=config.max_new_tokens,
            top_p=config.top_p if config.enable_top_p else None,
        )

        if (
            self.eval_llm_wrapper is None
            or config.model_name != self.eval_llm_model_name
        ):
            from llm_eval_framework.llm import LLMGenerationWrapper

            self.logger.info(
                "Loading evaluated LLM: %s (endpoint=%s)",
                config.model_name,
                config.endpoint or "local",
            )
            try:
                self.eval_llm_model_name = config.model_name
                self.eval_llm_wrapper = LLMGenerationWrapper(
                    model_name=config.model_name,
                    load_in_4bit=False,
                    load_in_8bit=False,
                    sampling_params=sampling_params,
                    endpoint=config.endpoint,
                )
            except Exception:
                self.logger.exception(
                    "Failed to load evaluated LLM '%s'", config.model_name
                )
                raise

        prompt = config.prompt
        if prompt is None or (isinstance(prompt, str) and not prompt.strip()):
            # NOTE: if prompt is None or empty string
            dataframe = self.get_input_data("dataset")

            if dataframe is None:
                self.logger.critical("Dataset input provider required but not set")
                raise Exception("Dataset input provider not set")

            if config.prompt_template is None:
                self.logger.critical("Prompt template required but not set but")
                raise Exception("Prompt template not set")

            assert isinstance(dataframe, pd.DataFrame)
            llm_dataset = LLMDataset(dataframe, config.prompt_template)
            it = llm_dataset.iter(config.batch_size)
            num_batches = math.ceil(len(llm_dataset) / config.batch_size)
        else:
            # (idx, row, prompt, answer)
            it = [([0], [{}], [prompt], [config.answer or None])]
            num_batches = 1

        outputs = []
        for i, batch in self.progress_bar(
            it,
            total=num_batches,
            start=1,
            with_index=True,
            desc="Computing LLM outputs",
        ):
            prompts = batch[2]
            self.logger.debug("Generating batch %d with %d prompts", i, len(prompts))
            try:
                llm_outputs = self.eval_llm_wrapper.generate(prompts)
            except Exception:
                self.logger.exception(
                    "Generation failed for batch %d (%d prompts)", i, len(prompts)
                )
                raise

            for idx, row, prompt, answer, llm_output in zip(*batch, llm_outputs):
                output = row.copy()
                output.update(
                    dict(
                        row_index=idx,
                        prompt=prompt,
                        answer=answer,
                        response=llm_output.content,
                    )
                )
                outputs.append(output)

        if self.eval_llm_wrapper is not None:
            self.logger.info("Unloading evaluated LLM")
            self.eval_llm_wrapper.unload()

        self.logger.info("Generated %d outputs", len(outputs))
        return outputs

    def evaluate(self, config_data: dict) -> list[dict]:
        import pandas as pd

        config = self.validate_config_form_data(config_data)

        self.logger.info("Starting evaluation (model=%s)", config.model_name)

        outputs = self.get_input_data("llm-predictions")

        if outputs is not None:
            self.logger.info(
                "Using pre-computed LLM predictions for heuristic and LLM-as-judge metrics."
            )
        else:
            outputs = self.compute_outputs(config)

        regex_pattern = config.regex_pattern.strip() or None
        heuristic_metrics = self._compute_heuristic_metrics(
            outputs, regex_pattern=regex_pattern
        )

        is_judge = (
            config.model_judge_name is not None
            and isinstance(config.model_judge_name, str)
            and config.model_judge_name.strip()
        )

        judge_metrics = (
            self._compute_judge_metrics(outputs, config)
            if is_judge
            else cycle((dict(),))
        )

        if not is_judge:
            self.logger.warning("No judge LLM configured, skipping judge metrics")

        for output, h_metrics, j_metrics in zip(
            outputs, heuristic_metrics, judge_metrics
        ):
            output.update({**h_metrics, **j_metrics})

        self.upload_artifact(
            "results.csv", pd.DataFrame(outputs).to_csv(index=False).encode("utf-8")
        )

        self.logger.info("Evaluation complete: %d outputs scored", len(outputs))
        return outputs

    def get_metric_visualizations(self, config_data: dict) -> list[MetricVisualization]:
        config = self.validate_config_form_data(config_data)

        table = MetricVisualization(
            chart_type=ChartType.TABLE, metrics=self.get_metrics()
        )

        is_multivalued = isinstance(config.prompt, str) and not config.prompt.strip()
        is_llm_as_a_judge = (
            config.model_judge_name is not None
            and isinstance(config.model_judge_name, str)
            and config.model_judge_name.strip()
        )

        if is_multivalued:
            charts = [
                MetricVisualization(
                    chart_type=ChartType.SCATTER,
                    metrics=self.metric_heuristic_names,
                ),
            ]
            if is_llm_as_a_judge:
                charts.append(
                    MetricVisualization(
                        chart_type=ChartType.SCATTER, metrics=self.metric_judge_names
                    )
                )
            _metrics = (
                self.metric_names()
                if is_llm_as_a_judge
                else self.metric_heuristic_names
            )
            charts.extend(
                MetricVisualization(chart_type=ChartType.KDE, metrics=[m])
                for m in _metrics
            )
        else:
            charts = [
                MetricVisualization(
                    chart_type=ChartType.RADAR, metrics=self.metric_heuristic_names
                )
            ]
            if is_llm_as_a_judge:
                charts.append(
                    MetricVisualization(
                        chart_type=ChartType.RADAR, metrics=self.metric_judge_names
                    )
                )

        return [table, *charts]
