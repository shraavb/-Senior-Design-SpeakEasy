"""
Catalan-Accented Spanish Dataset Pipeline
For building LLM fine-tuning datasets from movie subtitles.
"""

from .subtitle_downloader import OpenSubtitlesClient, OPUSCorpusDownloader
from .dialog_extractor import SubtitleParser, DialogEntry, batch_extract_dialogs
from .scenario_classifier import (
    KeywordClassifier,
    SemanticClassifier,
    HybridClassifier,
    classify_dialogs
)
from .dataset_formatter import DatasetFormatter, EvalSetGenerator, process_dataset

__all__ = [
    'OpenSubtitlesClient',
    'OPUSCorpusDownloader',
    'SubtitleParser',
    'DialogEntry',
    'batch_extract_dialogs',
    'KeywordClassifier',
    'SemanticClassifier',
    'HybridClassifier',
    'classify_dialogs',
    'DatasetFormatter',
    'EvalSetGenerator',
    'process_dataset',
]
