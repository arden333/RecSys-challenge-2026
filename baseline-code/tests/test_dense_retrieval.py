import unittest
from types import SimpleNamespace

import torch

from mcrs.retrieval_modules.dense import DenseRetriever


class FakeTokenizer:
    def __call__(self, texts, **kwargs):
        lengths = [len(text.split()) + 1 for text in texts]
        width = max(lengths)
        ids = torch.zeros((len(texts), width), dtype=torch.long)
        mask = torch.zeros_like(ids)
        for row, length in enumerate(lengths):
            ids[row, :length] = torch.arange(1, length + 1)
            mask[row, :length] = 1
        return {"input_ids": ids, "attention_mask": mask}


class FakeModel:
    def __call__(self, input_ids, attention_mask):
        values = input_ids.float()
        hidden = torch.stack((values, values.square()), dim=-1)
        return SimpleNamespace(last_hidden_state=hidden)


class DenseRetrieverTests(unittest.TestCase):
    def make_retriever(self, retrieval_type, max_length=10):
        retriever = DenseRetriever.__new__(DenseRetriever)
        retriever.retrieval_type = retrieval_type
        retriever.device = torch.device("cpu")
        retriever.max_length = max_length
        retriever.tokenizer = FakeTokenizer()
        retriever.model = FakeModel()
        retriever.query_instruction = "Retrieve music tracks."
        return retriever

    def test_bge_uses_first_token(self):
        retriever = self.make_retriever("bge_m3")
        vector = retriever._encode(["one two"])
        self.assertTrue(torch.allclose(vector[0], torch.tensor([1.0, 1.0]) / 2**0.5))

    def test_qwen_uses_last_non_padding_token_and_instruction(self):
        retriever = self.make_retriever("qwen3")
        self.assertEqual(
            retriever._query_text("user: upbeat song"),
            "Instruct: Retrieve music tracks.\nQuery:user: upbeat song",
        )
        vectors = retriever._encode(["one two three", "one"])
        self.assertEqual(vectors.shape, (2, 2))
        self.assertTrue(torch.allclose(vectors[1], torch.tensor([2.0, 4.0]) / 20**0.5))

    def test_overlong_input_is_rejected(self):
        retriever = self.make_retriever("bge_m3", max_length=2)
        with self.assertRaisesRegex(ValueError, "refusing to truncate"):
            retriever._encode(["one two three"])


if __name__ == "__main__":
    unittest.main()
