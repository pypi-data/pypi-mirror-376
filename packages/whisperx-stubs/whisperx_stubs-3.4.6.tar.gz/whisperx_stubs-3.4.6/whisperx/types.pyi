from typing import TypedDict

class SingleWordSegment(TypedDict):
    word: str
    start: float
    end: float
    score: float

class SingleCharSegment(TypedDict):
    char: str
    start: float
    end: float
    score: float

class SingleSegment(TypedDict):
    start: float
    end: float
    text: str

class SegmentData(TypedDict):
    clean_char: list[str]
    clean_cdx: list[int]
    clean_wdx: list[int]
    sentence_spans: list[tuple[int, int]]

class SingleAlignedSegment(TypedDict):
    start: float
    end: float
    text: str
    words: list[SingleWordSegment]
    chars: list[SingleCharSegment] | None

class TranscriptionResult(TypedDict):
    segments: list[SingleSegment]
    language: str

class AlignedTranscriptionResult(TypedDict):
    segments: list[SingleAlignedSegment]
    word_segments: list[SingleWordSegment]
