from _typeshed import Incomplete
from whisperx.conjunctions import (
    get_comma as get_comma,
    get_conjunctions as get_conjunctions,
)

def normal_round(n): ...
def format_timestamp(seconds: float, is_vtt: bool = False): ...

class SubtitlesProcessor:
    comma: Incomplete
    conjunctions: Incomplete
    segments: Incomplete
    lang: Incomplete
    max_line_length: Incomplete
    min_char_length_splitter: Incomplete
    is_vtt: Incomplete
    def __init__(
        self,
        segments,
        lang,
        max_line_length: int = 45,
        min_char_length_splitter: int = 30,
        is_vtt: bool = False,
    ) -> None: ...
    def estimate_timestamp_for_word(
        self, words, i, next_segment_start_time=None
    ) -> None: ...
    def process_segments(self, advanced_splitting: bool = True): ...
    def determine_advanced_split_points(
        self, segment, next_segment_start_time=None
    ): ...
    def generate_subtitles_from_split_points(
        self, segment, split_points, next_start_time=None
    ): ...
    def save(
        self, filename: str = "subtitles.srt", advanced_splitting: bool = True
    ): ...
