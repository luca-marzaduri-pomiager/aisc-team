"""Tests for aisc_plugin_llm_eval.utils (get_items, add_metrics)."""

from aisc_plugin_interface.models.measure import Measure

from aisc_plugin_llm_eval.utils import add_metrics, get_items


class TestGetItemsSingleMode:
    """get_items with batch=False (default) returns a flat tuple."""

    def test_single_index(self):
        data = ["a", "b", "c"]
        assert get_items(data, 1) == ("b",)

    def test_multiple_indices(self):
        data = ["a", "b", "c", "d"]
        assert get_items(data, 0, 3) == ("a", "d")

    def test_all_indices(self):
        data = [10, 20, 30]
        assert get_items(data, 0, 1, 2) == (10, 20, 30)

    def test_no_indices_returns_empty(self):
        data = [1, 2, 3]
        assert get_items(data) == ()

    def test_with_tuples(self):
        data = [(1, "a"), (2, "b"), (3, "c")]
        assert get_items(data, 0, 2) == ((1, "a"), (3, "c"))


class TestGetItemsBatchMode:
    """get_items with batch=True transposes rows into columns."""

    def test_batch_multiple_indices(self):
        data = [(1, "a"), (2, "b"), (3, "c")]
        result = get_items(data, 0, 2, batch=True)
        assert result == ((1, 3), ("a", "c"))

    def test_batch_single_index(self):
        data = [(1, "a"), (2, "b")]
        result = get_items(data, 1, batch=True)
        assert result == ((2,), ("b",))

    def test_batch_no_indices(self):
        assert get_items([(1, 2)], batch=True) == ()

    def test_batch_all_indices(self):
        data = [(10, "x"), (20, "y"), (30, "z")]
        result = get_items(data, 0, 1, 2, batch=True)
        assert result == ((10, 20, 30), ("x", "y", "z"))


class TestAddMetrics:
    """The @add_metrics decorator dynamically adds export_metric_* methods."""

    def _make_decorated_class(self, names: list[str]):
        """Create a minimal class decorated with @add_metrics."""

        @add_metrics
        class Dummy:
            @classmethod
            def metric_names(cls):
                return names

        return Dummy

    def test_methods_created(self):
        cls = self._make_decorated_class(["bleu", "rouge"])
        assert hasattr(cls, "export_metric_bleu")
        assert hasattr(cls, "export_metric_rouge")

    def test_methods_have_metric_name_attribute(self):
        cls = self._make_decorated_class(["bleu"])
        method = cls.export_metric_bleu
        assert hasattr(method, "metric_name")
        assert method.metric_name == "bleu"

    def test_export_returns_measures(self):
        cls = self._make_decorated_class(["bleu"])
        instance = cls()
        evaluation_output = [{"bleu": 0.85}, {"bleu": 0.72}]
        measures = instance.export_metric_bleu(evaluation_output)
        assert len(measures) == 2
        assert all(isinstance(m, Measure) for m in measures)
        assert measures[0].score == 0.85
        assert measures[1].score == 0.72

    def test_export_skips_none_scores(self):
        cls = self._make_decorated_class(["bleu"])
        instance = cls()
        evaluation_output = [{"bleu": None}, {"bleu": 0.5}]
        measures = instance.export_metric_bleu(evaluation_output)
        assert len(measures) == 1
        assert measures[0].score == 0.5

    def test_export_skips_missing_metric(self):
        cls = self._make_decorated_class(["bleu"])
        instance = cls()
        evaluation_output = [{"rouge": 0.9}]
        measures = instance.export_metric_bleu(evaluation_output)
        assert measures == []

    def test_description_set_for_multi_output(self):
        cls = self._make_decorated_class(["bleu"])
        instance = cls()
        evaluation_output = [{"bleu": 0.8}, {"bleu": 0.6}]
        measures = instance.export_metric_bleu(evaluation_output)
        # description is str(i) when len > 1
        assert measures[0].description == "0"
        assert measures[1].description == "1"

    def test_description_none_for_single_output(self):
        cls = self._make_decorated_class(["bleu"])
        instance = cls()
        evaluation_output = [{"bleu": 0.8}]
        measures = instance.export_metric_bleu(evaluation_output)
        assert measures[0].description is None

    def test_empty_metric_names(self):
        cls = self._make_decorated_class([])
        # No export methods added, class still works
        assert not hasattr(cls, "export_metric_bleu")
