from .bm25 import BM25_MODEL
from .bert import BERT_MODEL
from .dense import DenseRetriever

def load_retrieval_module(
        retrieval_type: str,
        dataset_name: str,
        track_split_types: list[str],
        corpus_types: list[str] = ["track_name", "artist_name", "album_name"],
        cache_dir: str = "./cache",
        model_name: str | None = None,
        device: str = "cpu",
        max_length: int | None = None,
        batch_size: int = 4,
        query_instruction: str | None = None,
    ):
    if retrieval_type == "bm25":
        return BM25_MODEL(dataset_name, track_split_types, corpus_types, cache_dir)
    elif retrieval_type == "bert":
        return BERT_MODEL(dataset_name, track_split_types, corpus_types, cache_dir)
    elif retrieval_type in {"bge_m3", "qwen3"}:
        if model_name is None or max_length is None:
            raise ValueError("Dense retrieval requires model_name and max_length")
        return DenseRetriever(
            dataset_name, track_split_types, corpus_types, cache_dir,
            retrieval_type, model_name, device, max_length, batch_size, query_instruction,
        )
    else:
        raise ValueError(f"Unsupported retrieval type: {retrieval_type}")
