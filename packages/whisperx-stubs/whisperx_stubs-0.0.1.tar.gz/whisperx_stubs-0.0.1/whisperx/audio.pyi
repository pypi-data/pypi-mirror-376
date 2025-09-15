import numpy as np
import torch
from _typeshed import Incomplete
from whisperx.utils import exact_div as exact_div

SAMPLE_RATE: int
N_FFT: int
HOP_LENGTH: int
CHUNK_LENGTH: int
N_SAMPLES: Incomplete
N_FRAMES: Incomplete
N_SAMPLES_PER_TOKEN: Incomplete
FRAMES_PER_SECOND: Incomplete
TOKENS_PER_SECOND: Incomplete

def load_audio(file: str, sr: int = ...) -> np.ndarray: ...
def pad_or_trim(array, length: int = ..., *, axis: int = -1): ...
def mel_filters(device, n_mels: int) -> torch.Tensor: ...
def log_mel_spectrogram(
    audio: str | np.ndarray | torch.Tensor,
    n_mels: int,
    padding: int = 0,
    device: str | torch.device | None = None,
): ...
