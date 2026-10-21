from ..plugin import LLMEvaluationPlugin


class LLMEvaluationPluginForTranslation(LLMEvaluationPlugin):
    plugin_name = "Translation LLM Evaluation"

    ui_icon = "translate"

    form_ui_schema = {
        "prompt_template": {"ui:widget": "textarea", "ui:options": {"rows": 7}},
        "prompt": {"ui:widget": "textarea", "ui:options": {"rows": 7}},
        "text": {"ui:widget": "textarea"},
        "batch_size": {"ui:widget": "updown"},
        "temperature": {"ui:widget": "updown"},
        "max_new_tokens": {"ui:widget": "hidden"},
        "max_new_tokens_judge": {"ui:widget": "hidden"},
        "enable_top_p": {"ui:widget": "hidden"},
        "top_p": {"ui:widget": "hidden"},
        "enable_top_p_judge": {"ui:widget": "hidden"},
        "top_p_judge": {"ui:widget": "hidden"},
        "regex_pattern": {"ui:widget": "hidden"},
    }

    metric_heuristic_names = [
        "equals",
        "bleu",
        "rouge",
        "levenshtein",
        "anls",
    ]

    metric_judge_names = [
        "factual_accuracy",
        "answer_correctness",
        "bias",
        "safety",
        "instruction_following",
    ]
