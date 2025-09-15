import argparse
from whisperx.alignment import align as align, load_align_model as load_align_model
from whisperx.asr import load_model as load_model
from whisperx.audio import load_audio as load_audio
from whisperx.diarize import (
    DiarizationPipeline as DiarizationPipeline,
    assign_word_speakers as assign_word_speakers,
)
from whisperx.types import (
    AlignedTranscriptionResult as AlignedTranscriptionResult,
    TranscriptionResult as TranscriptionResult,
)
from whisperx.utils import (
    LANGUAGES as LANGUAGES,
    TO_LANGUAGE_CODE as TO_LANGUAGE_CODE,
    get_writer as get_writer,
)

def transcribe_task(args: dict, parser: argparse.ArgumentParser): ...
