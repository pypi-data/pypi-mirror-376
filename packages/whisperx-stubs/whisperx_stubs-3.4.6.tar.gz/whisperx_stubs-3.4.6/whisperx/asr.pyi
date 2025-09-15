import ctranslate2
import faster_whisper
import numpy as np
import torch
from _typeshed import Incomplete
from faster_whisper.tokenizer import Tokenizer
from faster_whisper.transcribe import TranscriptionOptions
from transformers import Pipeline
from whisperx.audio import (
    N_SAMPLES as N_SAMPLES,
    SAMPLE_RATE as SAMPLE_RATE,
    load_audio as load_audio,
    log_mel_spectrogram as log_mel_spectrogram,
)
from whisperx.types import (
    SingleSegment as SingleSegment,
    TranscriptionResult as TranscriptionResult,
)
from whisperx.vads import Pyannote as Pyannote, Silero as Silero, Vad as Vad

def find_numeral_symbol_tokens(tokenizer): ...

class WhisperModel(faster_whisper.WhisperModel):
    def generate_segment_batched(
        self,
        features: np.ndarray,
        tokenizer: Tokenizer,
        options: TranscriptionOptions,
        encoder_output=None,
    ): ...
    def encode(self, features: np.ndarray) -> ctranslate2.StorageView: ...

class FasterWhisperPipeline(Pipeline):
    model: Incomplete
    tokenizer: Incomplete
    options: Incomplete
    preset_language: Incomplete
    suppress_numerals: Incomplete
    call_count: int
    framework: Incomplete
    device: Incomplete
    vad_model: Incomplete
    def __init__(
        self,
        model: WhisperModel,
        vad,
        vad_params: dict,
        options: TranscriptionOptions,
        tokenizer: Tokenizer | None = None,
        device: int | str | torch.device = -1,
        framework: str = "pt",
        language: str | None = None,
        suppress_numerals: bool = False,
        **kwargs,
    ) -> None: ...
    def preprocess(self, audio): ...
    def postprocess(self, model_outputs): ...
    def get_iterator(
        self,
        inputs,
        num_workers: int,
        batch_size: int,
        preprocess_params: dict,
        forward_params: dict,
        postprocess_params: dict,
    ): ...
    def transcribe(
        self,
        audio: str | np.ndarray,
        batch_size: int | None = None,
        num_workers: int = 0,
        language: str | None = None,
        task: str | None = None,
        chunk_size: int = 30,
        print_progress: bool = False,
        combined_progress: bool = False,
        verbose: bool = False,
    ) -> TranscriptionResult: ...
    def detect_language(self, audio: np.ndarray) -> str: ...

def load_model(
    whisper_arch: str,
    device: str,
    device_index: int = 0,
    compute_type: str = "float16",
    asr_options: dict | None = None,
    language: str | None = None,
    vad_model: Vad | None = None,
    vad_method: str | None = "pyannote",
    vad_options: dict | None = None,
    model: WhisperModel | None = None,
    task: str = "transcribe",
    download_root: str | None = None,
    local_files_only: bool = False,
    threads: int = 4,
) -> FasterWhisperPipeline: ...
