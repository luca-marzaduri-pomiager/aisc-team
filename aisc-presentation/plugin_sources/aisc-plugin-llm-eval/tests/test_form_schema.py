"""Tests for aisc_plugin_llm_eval.form_schema.ConfigFormSchema."""

import pytest
from pydantic import ValidationError

from aisc_plugin_llm_eval.form_schema import ConfigFormSchema


class TestConfigFormSchemaDefaults:
    """Verify default values are applied correctly."""

    def test_defaults(self):
        schema = ConfigFormSchema()
        assert schema.endpoint == ""
        assert schema.prompt_template == ""
        assert schema.model_name == ""
        assert schema.batch_size == 1
        assert schema.temperature == 0.6
        assert schema.max_new_tokens == 512
        assert schema.enable_top_p is False
        assert schema.top_p == 0.9
        assert schema.prompt == ""
        assert schema.answer == ""
        assert schema.model_judge_name == ""
        assert schema.batch_size_judge == 1
        assert schema.retries_judge == 3
        assert schema.temperature_judge == 0.6
        assert schema.max_new_tokens_judge == 512
        assert schema.enable_top_p_judge is False
        assert schema.top_p_judge == 0.9


class TestConfigFormSchemaValid:
    """Valid input is accepted and values are preserved."""

    def test_valid_config(self, default_config_data):
        schema = ConfigFormSchema(**default_config_data)
        assert schema.model_name == "test-model/tiny"
        assert schema.batch_size == 1
        assert schema.temperature == 0.6
        assert schema.max_new_tokens == 64

    def test_with_judge_config(self, default_config_data):
        default_config_data["model_judge_name"] = "judge-model/small"
        default_config_data["batch_size_judge"] = 4
        default_config_data["retries_judge"] = 5
        schema = ConfigFormSchema(**default_config_data)
        assert schema.model_judge_name == "judge-model/small"
        assert schema.batch_size_judge == 4
        assert schema.retries_judge == 5


class TestConfigFormSchemaConstraints:
    """Field constraints (gt, ge, le, multiple_of) are enforced."""

    def test_batch_size_must_be_positive(self):
        with pytest.raises(ValidationError):
            ConfigFormSchema(batch_size=0)

    def test_batch_size_negative(self):
        with pytest.raises(ValidationError):
            ConfigFormSchema(batch_size=-1)

    def test_temperature_must_be_positive(self):
        with pytest.raises(ValidationError):
            ConfigFormSchema(temperature=0.0)

    def test_max_new_tokens_must_be_gt_1(self):
        with pytest.raises(ValidationError):
            ConfigFormSchema(max_new_tokens=1)

    def test_top_p_lower_bound(self):
        # ge=0.0, so 0.0 is valid
        schema = ConfigFormSchema(top_p=0.0)
        assert schema.top_p == 0.0

    def test_top_p_upper_bound(self):
        # le=1.0, so 1.0 is valid
        schema = ConfigFormSchema(top_p=1.0)
        assert schema.top_p == 1.0

    def test_top_p_exceeds_upper_bound(self):
        with pytest.raises(ValidationError):
            ConfigFormSchema(top_p=1.01)

    def test_top_p_below_lower_bound(self):
        with pytest.raises(ValidationError):
            ConfigFormSchema(top_p=-0.01)

    def test_judge_batch_size_must_be_positive(self):
        with pytest.raises(ValidationError):
            ConfigFormSchema(batch_size_judge=0)

    def test_judge_retries_must_be_positive(self):
        with pytest.raises(ValidationError):
            ConfigFormSchema(retries_judge=0)

    def test_judge_temperature_must_be_positive(self):
        with pytest.raises(ValidationError):
            ConfigFormSchema(temperature_judge=0.0)

    def test_judge_max_new_tokens_must_be_gt_1(self):
        with pytest.raises(ValidationError):
            ConfigFormSchema(max_new_tokens_judge=1)

    def test_top_p_judge_bounds(self):
        with pytest.raises(ValidationError):
            ConfigFormSchema(top_p_judge=1.5)


class TestConfigFormSchemaModelValidate:
    """model_validate (used by validate_config_form_data) works with dicts."""

    def test_model_validate_from_dict(self, default_config_data):
        schema = ConfigFormSchema.model_validate(default_config_data)
        assert schema.model_name == default_config_data["model_name"]

    def test_model_validate_with_extra_fields_ignored(self, default_config_data):
        """Extra fields should not cause errors (Pydantic default: ignore)."""
        default_config_data["unknown_field"] = "hello"
        # This will raise if model is configured with extra='forbid'
        # The current schema doesn't set extra, so extras are ignored by default
        schema = ConfigFormSchema.model_validate(default_config_data)
        assert schema.model_name == default_config_data["model_name"]
