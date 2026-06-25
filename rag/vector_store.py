
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, cast

import faiss
import numpy as np

from core.config import settings
from core.models import ChunkRecord, RetrievalHit
from rag.embeddings import Embedder


class FaissVectorStore:
    def __init__(self) -> None:
        self.embedder = Embedder()
        self.index: Any = None
        self.metadata: List[dict] = []
        self.index_path = Path(settings.vector_index_path)
        self.meta_path = Path(settings.vector_meta_path)

    def build(self, chunks: List[ChunkRecord]) -> None:
        texts = [chunk.text for chunk in chunks]
        vectors = self.embedder.encode(texts)

        dim = vectors.shape[1]
        self.index = faiss.IndexFlatIP(dim)

        index = cast(Any, self.index)
        index.add(vectors)

        self.metadata = [
            {
                "chunk_id": chunk.chunk_id,
                "source_file": chunk.source_file,
                "patient_name": chunk.patient_name,
                "text": chunk.text,
                "metadata": chunk.metadata,
            }
            for chunk in chunks
        ]

        self.save()

    def save(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        if self.index is not None:
            faiss.write_index(self.index, str(self.index_path))

        self.meta_path.write_text(
            json.dumps(self.metadata, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def load(self) -> bool:
        if self.index_path.exists() and self.meta_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            self.metadata = json.loads(self.meta_path.read_text(encoding="utf-8"))
            return True
        return False

    def search(
        self,
        query: str,
        top_k: int | None = None,
        patient_name: str | None = None,
    ) -> List[RetrievalHit]:
        if self.index is None:
            raise RuntimeError("Vector index not loaded/built")

        top_k = top_k or settings.retrieval_top_k
        query_vector = self.embedder.encode([query])

        index = cast(Any, self.index)
        scores, ids = index.search(query_vector, max(top_k * 4, top_k))

        hits: List[RetrievalHit] = []

        for score, idx in zip(scores[0], ids[0]):
            if idx == -1:
                continue

            meta = self.metadata[int(idx)]

            if patient_name and meta.get("patient_name"):
                if patient_name.lower() not in meta["patient_name"].lower():
                    continue

            hits.append(
                RetrievalHit(
                    chunk_id=meta["chunk_id"],
                    score=float(score),
                    source_file=meta["source_file"],
                    patient_name=meta.get("patient_name"),
                    text=meta["text"],
                    metadata=meta.get("metadata", {}),
                )
            )

            if len(hits) >= top_k:
                break

        return hits
