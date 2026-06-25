from __future__ import annotations
from sentence_transformers import SentenceTransformer
import numpy as np
from core.config import settings


class Embedder:
    def __init__(self) -> None:
        self.model = SentenceTransformer(settings.embedding_model,device="cpu")

    def encode(self, texts: list[str]) -> np.ndarray:
        vectors = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(vectors, dtype='float32')