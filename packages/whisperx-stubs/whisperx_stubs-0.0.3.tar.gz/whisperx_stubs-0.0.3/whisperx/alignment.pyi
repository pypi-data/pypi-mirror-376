import numpy as np
import torch
from _typeshed import Incomplete
from dataclasses import dataclass
from typing import Iterable
from whisperx.audio import SAMPLE_RATE as SAMPLE_RATE, load_audio as load_audio
from whisperx.types import (
    AlignedTranscriptionResult as AlignedTranscriptionResult,
    SegmentData as SegmentData,
    SingleAlignedSegment as SingleAlignedSegment,
    SingleSegment as SingleSegment,
    SingleWordSegment as SingleWordSegment,
)
from whisperx.utils import interpolate_nans as interpolate_nans

PUNKT_ABBREVIATIONS: Incomplete
LANGUAGES_WITHOUT_SPACES: Incomplete
DEFAULT_ALIGN_MODELS_TORCH: Incomplete
DEFAULT_ALIGN_MODELS_HF: Incomplete

def load_align_model(
    language_code: str, device: str, model_name: str | None = None, model_dir=None
): ...
def align(
    transcript: Iterable[SingleSegment],
    model: torch.nn.Module,
    align_model_metadata: dict,
    audio: str | np.ndarray | torch.Tensor,
    device: str,
    interpolate_method: str = "nearest",
    return_char_alignments: bool = False,
    print_progress: bool = False,
    combined_progress: bool = False,
) -> AlignedTranscriptionResult: ...
def get_trellis(emission, tokens, blank_id: int = 0): ...
def get_wildcard_emission(frame_emission, tokens, blank_id): ...
@dataclass
class Point:
    token_index: int
    time_index: int
    score: float

def backtrack(trellis, emission, tokens, blank_id: int = 0): ...
@dataclass
class Path:
    points: list[Point]
    score: float

@dataclass
class BeamState:
    token_index: int
    time_index: int
    score: float
    path: list[Point]

def backtrack_beam(
    trellis, emission, tokens, blank_id: int = 0, beam_width: int = 5
): ...
@dataclass
class Segment:
    label: str
    start: int
    end: int
    score: float
    @property
    def length(self): ...

def merge_repeats(path, transcript): ...
def merge_words(segments, separator: str = "|"): ...
