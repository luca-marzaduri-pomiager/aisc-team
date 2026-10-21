"""Tests for aisc_plugin_llm_eval.dataset_provider"""

from aisc_plugin_llm_eval.dataset_provider import DataFrameProvider


class TestDataFrameProvider:
    def test_provider(self, dataset, dataset_bytes):
        provider = DataFrameProvider(dataset_bytes)
        data = provider.get_data()

        assert data.shape == dataset.shape
        assert dataset.equals(data)


class TestLLMDatasetGetItem:
    def test_getitem_returns_tuple(self, llm_dataset):
        item = llm_dataset[0]
        assert isinstance(item, tuple)
        assert len(item) == 4  # (idx, row, prompt, answer)

    def test_getitem_idx_matches(self, llm_dataset):
        idx, row, prompt, answer = llm_dataset[1]
        assert idx == 1

    def test_getitem_row_is_dict(self, llm_dataset):
        _, row, _, _ = llm_dataset[0]
        assert isinstance(row, dict)
        assert "question" in row

    def test_getitem_prompt_uses_template(self, llm_dataset):
        """Prompt should render the template with row data."""
        _, _, prompt, _ = llm_dataset[0]
        assert isinstance(prompt, str)
        # template is "Question: {{question}}\nAnswer:", so prompt should contain the question
        assert "What is 1+1?" in prompt

    def test_getitem_answer(self, sample_rows, llm_dataset):
        _, _, _, answer = llm_dataset[1]
        assert answer == sample_rows[1]["answer"]


class TestLLMDatasetIter:
    def test_iter_yields_batches(self, llm_dataset):
        batches = list(llm_dataset.iter(batch_size=2))
        # 3 rows, batch_size=2 => 2 batches (2 + 1)
        assert len(batches) == 2

    def test_iter_batch_structure(self, llm_dataset):
        """Each batch is a tuple of columns: (indices, rows, prompts, answers)."""
        batch = next(iter(llm_dataset.iter(batch_size=3)))
        assert len(batch) == 4  # 4 columns
        indices, rows, prompts, answers = batch
        assert len(indices) == 3

    def test_iter_single_batch(self, llm_dataset):
        """batch_size >= len yields a single batch."""
        batches = list(llm_dataset.iter(batch_size=10))
        assert len(batches) == 1

    def test_iter_batch_size_one(self, llm_dataset):
        batches = list(llm_dataset.iter(batch_size=1))
        assert len(batches) == 3
