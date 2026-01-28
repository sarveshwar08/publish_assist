from functools import cached_property
from pathlib import Path
from typing import Optional

import numpy as np
from loguru import logger
from numpy.typing import NDArray
from sentence_transformers import SentenceTransformer
from sentence_transformers.cross_encoder import CrossEncoder
from transformers import AutoTokenizer

from publish_assist.settings import settings
from .base import SingletonMeta


class EmbeddingModelSingleton(metaclass=SingletonMeta):
    """
    Loads a SentenceTransformer model once and reuses it.
    """

    def __init__(
        self,
        model_id: str = settings.TEXT_EMBEDDING_MODEL_ID,
        device: str = settings.RAG_MODEL_DEVICE,
        cache_dir: Optional[Path] = None,
    ) -> None:
        self._model_id = model_id
        self._device = device

        self._model = SentenceTransformer(
            self._model_id,
            device=self._device,
            cache_folder=str(cache_dir) if cache_dir else None,
        )
        self._model.eval()

    @cached_property
    def embedding_size(self) -> int:
        return int(self._model.get_sentence_embedding_dimension())

    @property
    def tokenizer(self) -> AutoTokenizer:
        return self._model.tokenizer

    @property
    def max_input_length(self) -> int:
        return int(self._model.max_seq_length)
    
    @property
    def model_id(self) -> str:
        return self._model_id

    def embed(self, input_text: str | list[str]) -> list[float] | list[list[float]]:
        """
        Always return python list (Qdrant expects list[float]).
        """
        try:
            emb = self._model.encode(input_text, normalize_embeddings=True)
        except Exception:
            logger.exception(f"Error generating embeddings for model_id={self._model_id}")
            return [] if isinstance(input_text, str) else []

        return emb.tolist()


class CrossEncoderModelSingleton(metaclass=SingletonMeta):

    # for reranking
    
    def __init__(
        self,
        model_id: str = settings.RERANKING_CROSS_ENCODER_MODEL_ID,
        device: str = settings.RAG_MODEL_DEVICE,
    ) -> None:
        self._model_id = model_id
        self._device = device

        self._model = CrossEncoder(model_name=self._model_id, device=self._device)
        self._model.model.eval()

    def score(self, pairs: list[tuple[str, str]]) -> list[float]:
        scores = self._model.predict(pairs)
        return scores.tolist()
