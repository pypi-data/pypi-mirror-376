import numpy as np
import pandas as pd
import torch
from _typeshed import Incomplete
from typing import Literal, overload
from whisperx.audio import SAMPLE_RATE as SAMPLE_RATE, load_audio as load_audio
from whisperx.types import (
    AlignedTranscriptionResult as AlignedTranscriptionResult,
    TranscriptionResult as TranscriptionResult,
)

class DiarizationPipeline:
    model: Incomplete
    def __init__(
        self,
        model_name=None,
        use_auth_token=None,
        device: str | torch.device | None = "cpu",
    ) -> None: ...
    @overload
    def __call__(
        self,
        audio: str | np.ndarray,
        num_speakers: int | None = None,
        min_speakers: int | None = None,
        max_speakers: int | None = None,
        *,
        return_embeddings: Literal[True],
    ) -> tuple[pd.DataFrame, dict[str, list[float]] | None]: ...
    @overload
    def __call__(
        self,
        audio: str | np.ndarray,
        num_speakers: int | None = None,
        min_speakers: int | None = None,
        max_speakers: int | None = None,
        *,
        return_embeddings: Literal[False],
    ) -> pd.DataFrame: ...
    @overload
    def __call__(
        self,
        audio: str | np.ndarray,
        num_speakers: int | None = None,
        min_speakers: int | None = None,
        max_speakers: int | None = None,
    ) -> pd.DataFrame: ...

def assign_word_speakers(
    diarize_df: pd.DataFrame,
    transcript_result: AlignedTranscriptionResult | TranscriptionResult,
    speaker_embeddings: dict[str, list[float]] | None = None,
    fill_nearest: bool = False,
) -> AlignedTranscriptionResult | TranscriptionResult: ...

class Segment:
    start: Incomplete
    end: Incomplete
    speaker: Incomplete
    def __init__(self, start: int, end: int, speaker: str | None = None) -> None: ...
