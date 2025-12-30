"""
Dialog Extractor Module
Parses SRT subtitle files and extracts dialog with timestamps.
"""

import re
import srt
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import timedelta
import logging
import yaml
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DialogEntry:
    """Represents a single dialog entry with metadata."""
    id: str
    text: str
    start_time: timedelta
    end_time: timedelta
    source_file: str
    film_title: str = ""
    film_year: int = 0

    # Context
    context_before: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)

    # Classification (filled later)
    scenario: str = ""
    scenario_confidence: float = 0.0
    catalan_markers: List[str] = field(default_factory=list)

    @property
    def start_timestamp(self) -> str:
        """Format start time as HH:MM:SS,mmm"""
        return self._format_timedelta(self.start_time)

    @property
    def end_timestamp(self) -> str:
        """Format end time as HH:MM:SS,mmm"""
        return self._format_timedelta(self.end_time)

    @staticmethod
    def _format_timedelta(td: timedelta) -> str:
        """Format timedelta as SRT timestamp."""
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        milliseconds = int(td.microseconds / 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "text": self.text,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "duration_seconds": self.duration_seconds,
            "source_file": self.source_file,
            "film_title": self.film_title,
            "film_year": self.film_year,
            "context_before": self.context_before,
            "context_after": self.context_after,
            "scenario": self.scenario,
            "scenario_confidence": self.scenario_confidence,
            "catalan_markers": self.catalan_markers
        }


class SubtitleParser:
    """Parses SRT files and extracts clean dialog."""

    # Patterns to clean from subtitles
    CLEANING_PATTERNS = [
        r'<[^>]+>',           # HTML tags
        r'\{[^}]+\}',         # SSA/ASS style tags
        r'\[[^\]]+\]',        # Square bracket annotations [music], [applause]
        r'\([^)]+\)',         # Parenthetical annotations (sighing)
        r'♪[^♪]*♪',          # Music notes
        r'^-\s*',             # Leading dashes (speaker indicators)
        r'^\s*\d+\s*$',       # Standalone numbers
        r'http[s]?://\S+',    # URLs
        r'^#{1,}',            # Hash marks
    ]

    # Patterns indicating non-dialog content
    NON_DIALOG_PATTERNS = [
        r'^[A-Z\s]+:$',           # ALL CAPS labels (NARRATOR:)
        r'^\[.*\]$',              # Full line annotations
        r'^\(.*\)$',              # Full line parentheticals
        r'^♪.*$',                 # Music lines
        r'^[-—]+$',               # Just dashes
        r'^\.\.\.$',              # Just ellipsis
        r'^[.!?,;:\'"]+$',        # Just punctuation
    ]

    def __init__(self, config_path: str = "config/settings.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.min_length = self.config['processing']['min_dialog_length']
        self.max_length = self.config['processing']['max_dialog_length']
        self.context_lines = self.config['processing']['context_lines']

    def parse_srt_file(self, filepath: str) -> List[srt.Subtitle]:
        """Parse an SRT file and return subtitle objects."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try alternative encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                logger.error(f"Could not decode {filepath}")
                return []

        try:
            return list(srt.parse(content))
        except Exception as e:
            logger.error(f"Failed to parse SRT {filepath}: {e}")
            return []

    def clean_text(self, text: str) -> str:
        """Clean subtitle text by removing annotations and formatting."""
        cleaned = text

        # Apply cleaning patterns
        for pattern in self.CLEANING_PATTERNS:
            cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE | re.IGNORECASE)

        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()

        # Remove multiple punctuation
        cleaned = re.sub(r'([.!?])\1+', r'\1', cleaned)

        return cleaned

    def is_valid_dialog(self, text: str) -> bool:
        """Check if text represents valid dialog."""
        # Check length
        if len(text) < self.min_length or len(text) > self.max_length:
            return False

        # Check for non-dialog patterns
        for pattern in self.NON_DIALOG_PATTERNS:
            if re.match(pattern, text, re.IGNORECASE):
                return False

        # Must contain some letters
        if not re.search(r'[a-záéíóúñüà]', text, re.IGNORECASE):
            return False

        return True

    def extract_dialogs(
        self,
        filepath: str,
        film_title: str = "",
        film_year: int = 0
    ) -> List[DialogEntry]:
        """
        Extract clean dialog entries from an SRT file.

        Args:
            filepath: Path to the SRT file
            film_title: Title of the film (for metadata)
            film_year: Year of the film (for metadata)

        Returns:
            List of DialogEntry objects
        """
        subtitles = self.parse_srt_file(filepath)
        if not subtitles:
            return []

        dialogs = []
        source_name = Path(filepath).stem

        # Extract film info from filename if not provided
        if not film_title:
            # Try to parse from filename: "Title_Year_ID.srt"
            parts = source_name.rsplit('_', 2)
            if len(parts) >= 2:
                film_title = parts[0].replace('_', ' ')
                try:
                    film_year = int(parts[1])
                except ValueError:
                    pass

        # Process each subtitle
        for i, sub in enumerate(subtitles):
            # Clean the text
            cleaned_text = self.clean_text(sub.content)

            # Validate dialog
            if not self.is_valid_dialog(cleaned_text):
                continue

            # Get context (surrounding lines)
            context_before = []
            context_after = []

            for j in range(max(0, i - self.context_lines), i):
                ctx_text = self.clean_text(subtitles[j].content)
                if ctx_text:
                    context_before.append(ctx_text)

            for j in range(i + 1, min(len(subtitles), i + 1 + self.context_lines)):
                ctx_text = self.clean_text(subtitles[j].content)
                if ctx_text:
                    context_after.append(ctx_text)

            # Create dialog entry
            dialog = DialogEntry(
                id=f"{source_name}_{sub.index}",
                text=cleaned_text,
                start_time=sub.start,
                end_time=sub.end,
                source_file=filepath,
                film_title=film_title,
                film_year=film_year,
                context_before=context_before,
                context_after=context_after
            )

            dialogs.append(dialog)

        logger.info(f"Extracted {len(dialogs)} dialogs from {filepath}")
        return dialogs

    def merge_consecutive_dialogs(
        self,
        dialogs: List[DialogEntry],
        max_gap_seconds: float = 2.0
    ) -> List[DialogEntry]:
        """
        Merge consecutive dialog entries that are close together.
        This creates more natural conversation segments.
        """
        if not dialogs:
            return []

        merged = []
        current = dialogs[0]

        for next_dialog in dialogs[1:]:
            # Check if from same source
            if current.source_file != next_dialog.source_file:
                merged.append(current)
                current = next_dialog
                continue

            # Check time gap
            gap = (next_dialog.start_time - current.end_time).total_seconds()

            if gap <= max_gap_seconds:
                # Merge dialogs
                current = DialogEntry(
                    id=current.id,
                    text=f"{current.text} {next_dialog.text}",
                    start_time=current.start_time,
                    end_time=next_dialog.end_time,
                    source_file=current.source_file,
                    film_title=current.film_title,
                    film_year=current.film_year,
                    context_before=current.context_before,
                    context_after=next_dialog.context_after
                )
            else:
                merged.append(current)
                current = next_dialog

        merged.append(current)

        logger.info(f"Merged {len(dialogs)} dialogs into {len(merged)} segments")
        return merged


class CatalanMarkerDetector:
    """Detects Catalan linguistic markers in Spanish text."""

    def __init__(self, config_path: str = "config/settings.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.markers = self.config.get('catalan_markers', {})

    def detect_markers(self, text: str) -> List[str]:
        """
        Detect Catalan markers in text.

        Returns list of found markers.
        """
        found_markers = []
        text_lower = text.lower()

        # Check lexical borrowings
        for marker in self.markers.get('lexical_borrowings', []):
            if marker.lower() in text_lower:
                found_markers.append(f"lexical:{marker}")

        # Check syntactic patterns
        for pattern in self.markers.get('syntactic_patterns', []):
            if pattern.lower() in text_lower:
                found_markers.append(f"syntactic:{pattern}")

        return found_markers

    def calculate_catalan_score(self, text: str) -> float:
        """
        Calculate a score indicating likelihood of Catalan influence.
        Range: 0.0 to 1.0
        """
        markers = self.detect_markers(text)

        if not markers:
            return 0.0

        # Simple scoring: more markers = higher score
        max_markers = 5  # Normalize to this
        score = min(len(markers) / max_markers, 1.0)

        return score


def batch_extract_dialogs(
    srt_directory: str,
    output_file: str = "data/processed/all_dialogs.json",
    config_path: str = "config/settings.yaml"
) -> List[DialogEntry]:
    """
    Extract dialogs from all SRT files in a directory.

    Args:
        srt_directory: Directory containing SRT files
        output_file: Path to save extracted dialogs
        config_path: Path to configuration file

    Returns:
        List of all extracted DialogEntry objects
    """
    parser = SubtitleParser(config_path)
    marker_detector = CatalanMarkerDetector(config_path)

    srt_dir = Path(srt_directory)
    all_dialogs = []

    # Find all SRT files
    srt_files = list(srt_dir.glob("*.srt"))
    logger.info(f"Found {len(srt_files)} SRT files in {srt_directory}")

    for srt_file in srt_files:
        # Extract dialogs
        dialogs = parser.extract_dialogs(str(srt_file))

        # Detect Catalan markers
        for dialog in dialogs:
            dialog.catalan_markers = marker_detector.detect_markers(dialog.text)

        all_dialogs.extend(dialogs)

    # Optionally merge consecutive dialogs
    # all_dialogs = parser.merge_consecutive_dialogs(all_dialogs)

    # Save to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(
            [d.to_dict() for d in all_dialogs],
            f,
            ensure_ascii=False,
            indent=2
        )

    logger.info(f"Saved {len(all_dialogs)} dialogs to {output_file}")
    return all_dialogs


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) > 1:
        srt_path = sys.argv[1]
        parser = SubtitleParser()
        dialogs = parser.extract_dialogs(srt_path)

        print(f"\nExtracted {len(dialogs)} dialogs:")
        for d in dialogs[:5]:
            print(f"\n[{d.start_timestamp} -> {d.end_timestamp}]")
            print(f"  {d.text}")
            if d.catalan_markers:
                print(f"  Markers: {d.catalan_markers}")
    else:
        # Batch process
        batch_extract_dialogs("data/raw", "data/processed/all_dialogs.json")
