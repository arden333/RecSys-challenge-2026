"""Dense track retrieval with model-specific pooling and query formatting."""

import json
from pathlib import Path

import torch
import torch.nn.functional as F
from datasets import concatenate_datasets, load_dataset
from transformers import AutoModel, AutoTokenizer


class DenseRetriever:
    def __init__(
        self,
        dataset_name: str,
        split_types: list[str],
        corpus_types: list[str],
        cache_dir: str,
        retrieval_type: str,
        model_name: str,
        device: str,
        max_length: int,
        batch_size: int,
        query_instruction: str | None = None,
    ) -> None:
        if retrieval_type not in {"bge_m3", "qwen3"}:
            raise ValueError(f"Unsupported dense retriever: {retrieval_type}")
        if max_length < 1 or batch_size < 1:
            raise ValueError("max_length and batch_size must be positive")
        if retrieval_type == "qwen3" and not query_instruction:
            raise ValueError("Qwen3 requires a query instruction")

        self.retrieval_type = retrieval_type
        self.model_name = model_name
        self.device = torch.device(device)
        self.max_length = max_length
        self.batch_size = batch_size
        self.query_instruction = query_instruction
        model_cache = str(Path(cache_dir) / "hf")
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name, cache_dir=model_cache, use_fast=True
        )
        self.model = AutoModel.from_pretrained(
            model_name, cache_dir=model_cache
        ).to(self.device).eval()

        fields = "_".join(corpus_types)
        model_dir = model_name.replace("/", "__")
        self.index_dir = Path(cache_dir) / "dense" / model_dir / fields / str(max_length)
        vectors_path = self.index_dir / "embeddings.pt"
        ids_path = self.index_dir / "track_ids.json"
        if vectors_path.exists() and ids_path.exists():
            self.embeddings = torch.load(vectors_path, map_location="cpu", weights_only=True)
            self.track_ids = json.loads(ids_path.read_text(encoding="utf-8"))
        else:
            dataset = load_dataset(dataset_name)
            catalog = concatenate_datasets([dataset[split] for split in split_types])
            self.track_ids = [item["track_id"] for item in catalog]
            documents = [self._track_document(item, corpus_types) for item in catalog]
            self.embeddings = self._build_index(documents)
            self.index_dir.mkdir(parents=True, exist_ok=True)
            torch.save(self.embeddings, vectors_path)
            ids_path.write_text(json.dumps(self.track_ids), encoding="utf-8")

    @staticmethod
    def _track_document(track: dict, fields: list[str]) -> str:
        lines = []
        for field in fields:
            value = track[field]
            if isinstance(value, list):
                value = ", ".join(value)
            lines.append(f"{field}: {value}")
        return "\n".join(lines) + "\n"

    def _query_text(self, query: str) -> str:
        if self.retrieval_type == "qwen3":
            return f"Instruct: {self.query_instruction}\nQuery:{query}"
        return query

    def _encode(self, texts: list[str]) -> torch.Tensor:
        tokens = self.tokenizer(texts, padding=True, truncation=False, return_tensors="pt")
        observed_length = tokens["input_ids"].shape[1]
        if observed_length > self.max_length:
            raise ValueError(
                f"Input has {observed_length} tokens, above the configured {self.max_length}; "
                "refusing to truncate"
            )
        tokens = {key: value.to(self.device) for key, value in tokens.items()}
        with torch.inference_mode():
            output = self.model(**tokens).last_hidden_state
            if self.retrieval_type == "bge_m3":
                pooled = output[:, 0]
            else:
                if tokens["attention_mask"][:, -1].all():
                    pooled = output[:, -1]
                else:
                    last_positions = tokens["attention_mask"].sum(dim=1) - 1
                    row_positions = torch.arange(len(texts), device=self.device)
                    pooled = output[row_positions, last_positions]
            return F.normalize(pooled.float(), p=2, dim=1).cpu()

    def _build_index(self, documents: list[str]) -> torch.Tensor:
        lengths = []
        for start in range(0, len(documents), 256):
            lengths.extend(self.tokenizer(
                documents[start:start + 256], padding=False,
                truncation=False, return_length=True,
            )["length"])
        if max(lengths) > self.max_length:
            raise ValueError("Catalog document exceeds configured max_length")
        order = sorted(range(len(documents)), key=lengths.__getitem__)
        vectors = torch.empty((len(documents), self.model.config.hidden_size), dtype=torch.float32)
        for start in range(0, len(order), self.batch_size):
            positions = order[start:start + self.batch_size]
            batch_vectors = self._encode([documents[position] for position in positions])
            vectors[positions] = batch_vectors
            if start % 2000 < self.batch_size:
                print(f"Indexed {min(start + self.batch_size, len(order))}/{len(order)} tracks", flush=True)
        return vectors

    def batch_text_to_item_retrieval(self, queries: list[str], topk: int) -> list[list[str]]:
        if not queries:
            return []
        query_vectors = self._encode([self._query_text(query) for query in queries])
        scores = query_vectors @ self.embeddings.T
        k = min(topk, len(self.track_ids))
        top_positions = torch.topk(scores, k=k, dim=1).indices.tolist()
        return [[self.track_ids[position] for position in positions] for positions in top_positions]

    def text_to_item_retrieval(self, query: str, topk: int) -> list[str]:
        return self.batch_text_to_item_retrieval([query], topk)[0]
