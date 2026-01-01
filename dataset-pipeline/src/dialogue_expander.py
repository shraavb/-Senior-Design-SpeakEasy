#!/usr/bin/env python3
"""
Dialogue Expander Module

Creates longer multi-turn dialogues (5-7 lines per speaker) using two approaches:
1. LLM Expansion: Expands short dialogues into full conversations using Claude API
2. Subtitle Merger: Merges consecutive subtitle entries from movies into longer conversations

Output:
- dialogues_expanded_training.json: LLM-expanded dialogues for model fine-tuning
- dialogues_merged_eval.json: Merged authentic movie dialogues for user evaluation
"""

import json
import os
import re
import srt
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
from datetime import timedelta

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# LLM EXPANSION (Training Set)
# ============================================================================

class DialogueExpander:
    """
    Expands short dialogues into multi-turn conversations using Claude API.
    Target: 5-7 lines per speaker (10-14 total exchanges).
    """

    SYSTEM_PROMPT = """You are an expert in Spanish conversational dialogue, particularly Catalan-accented Spanish from Barcelona.
Your task is to expand a short dialogue snippet into a natural, multi-turn conversation.

Requirements:
1. Create a conversation with 5-7 lines per speaker (10-14 total exchanges)
2. Maintain the CEFR complexity level specified
3. Include Catalan/Spanish regional markers where natural (ey, apa, home, nen/nena, vale, guay, etc.)
4. Keep the conversation natural and coherent
5. Stay within the scenario context (greetings, farewells, family, emotions, etc.)
6. Use appropriate formality (tú vs usted based on context)

CEFR Level Guidelines:
- A1-A2: Present tense, simple sentences, basic vocabulary
- B1: Multiple tenses, compound sentences, opinion expressions
- B2: Subjunctive, complex clauses, abstract vocabulary
- C1-C2: Literary constructions, sophisticated discourse markers

Respond ONLY with valid JSON in this exact format:
{
    "conversation": [
        {"speaker": "A", "text": "..."},
        {"speaker": "B", "text": "..."},
        ...
    ],
    "catalan_markers": ["marker1", "marker2", ...]
}"""

    def __init__(self, api_key: Optional[str] = None):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package required. Run: pip install anthropic")

        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY required")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        logger.info("Initialized Claude API client for dialogue expansion")

    def expand(
        self,
        dialogue: Dict,
        target_lines_per_speaker: int = 6
    ) -> Dict:
        """
        Expand a short dialogue into a multi-turn conversation.

        Args:
            dialogue: Dict with ground_truth, context_before, context_after, scenario, cefr_level
            target_lines_per_speaker: Target number of lines per speaker (5-7)

        Returns:
            Dict with expanded conversation
        """
        ground_truth = dialogue.get("ground_truth", "")
        context_before = dialogue.get("context_before", [])
        context_after = dialogue.get("context_after", [])
        scenario = dialogue.get("scenario", "general")
        cefr_level = dialogue.get("cefr_level", "B1")

        user_prompt = f"""Expand this dialogue into a full conversation with {target_lines_per_speaker} lines per speaker.

Scenario: {scenario}
CEFR Level: {cefr_level}

Context before:
{chr(10).join(context_before) if context_before else "(none)"}

Original dialogue:
"{ground_truth}"

Context after:
{chr(10).join(context_after) if context_after else "(none)"}

Create a natural, flowing conversation that incorporates the original dialogue.
The conversation should have {target_lines_per_speaker * 2} total exchanges (alternating A and B).
Respond with JSON only."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}]
            )

            response_text = response.content[0].text.strip()

            # Handle markdown code blocks
            if response_text.startswith("```"):
                response_text = re.sub(r'^```json?\n?', '', response_text)
                response_text = re.sub(r'\n?```$', '', response_text)

            result = json.loads(response_text)

            return {
                "id": dialogue.get("id", ""),
                "scenario": scenario,
                "cefr_level": cefr_level,
                "cefr_simplified": dialogue.get("cefr_simplified", ""),
                "conversation": result.get("conversation", []),
                "catalan_markers": result.get("catalan_markers", []),
                "source_dialogue": ground_truth,
                "source_context_before": context_before,
                "source_context_after": context_after,
                "source_film": dialogue.get("source_film", ""),
                "expansion_method": "llm"
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return self._create_fallback(dialogue)
        except Exception as e:
            logger.error(f"API error: {e}")
            return self._create_fallback(dialogue)

    def _create_fallback(self, dialogue: Dict) -> Dict:
        """Create fallback when expansion fails."""
        return {
            "id": dialogue.get("id", ""),
            "scenario": dialogue.get("scenario", ""),
            "cefr_level": dialogue.get("cefr_level", ""),
            "cefr_simplified": dialogue.get("cefr_simplified", ""),
            "conversation": [
                {"speaker": "A", "text": line}
                for line in dialogue.get("context_before", [])
            ] + [
                {"speaker": "B", "text": dialogue.get("ground_truth", "")}
            ] + [
                {"speaker": "A", "text": line}
                for line in dialogue.get("context_after", [])
            ],
            "catalan_markers": [],
            "source_dialogue": dialogue.get("ground_truth", ""),
            "source_film": dialogue.get("source_film", ""),
            "expansion_method": "fallback"
        }

    def expand_batch(
        self,
        dialogues: List[Dict],
        target_lines_per_speaker: int = 6,
        show_progress: bool = True
    ) -> List[Dict]:
        """Expand a batch of dialogues."""
        results = []

        if show_progress:
            try:
                from tqdm import tqdm
                dialogues_iter = tqdm(dialogues, desc="Expanding dialogues")
            except ImportError:
                dialogues_iter = dialogues
        else:
            dialogues_iter = dialogues

        for dialogue in dialogues_iter:
            expanded = self.expand(dialogue, target_lines_per_speaker)
            results.append(expanded)

        return results


# ============================================================================
# SUBTITLE MERGER (Evaluation Set)
# ============================================================================

@dataclass
class ConversationSegment:
    """A merged conversation segment from subtitles."""
    id: str
    source_film: str
    timestamp_start: str
    timestamp_end: str
    conversation: List[Dict]
    total_lines: int
    duration_seconds: float


class SubtitleMerger:
    """
    Merges consecutive subtitle entries into longer conversations.
    Target: 10-14 lines per conversation (5-7 per speaker).
    """

    def __init__(
        self,
        min_lines: int = 10,
        max_lines: int = 16,
        max_gap_seconds: float = 3.0,
        speaker_gap_seconds: float = 1.0
    ):
        """
        Args:
            min_lines: Minimum lines required for a valid conversation
            max_lines: Maximum lines before starting a new segment
            max_gap_seconds: Maximum gap between subtitles to merge
            speaker_gap_seconds: Gap threshold to switch speakers
        """
        self.min_lines = min_lines
        self.max_lines = max_lines
        self.max_gap_seconds = max_gap_seconds
        self.speaker_gap_seconds = speaker_gap_seconds

    def parse_srt(self, filepath: str) -> List[srt.Subtitle]:
        """Parse an SRT file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
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
            logger.error(f"Failed to parse {filepath}: {e}")
            return []

    def clean_text(self, text: str) -> str:
        """Clean subtitle text."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove SSA/ASS tags
        text = re.sub(r'\{[^}]+\}', '', text)
        # Remove square bracket annotations
        text = re.sub(r'\[[^\]]+\]', '', text)
        # Remove parenthetical annotations
        text = re.sub(r'\([^)]+\)', '', text)
        # Remove music notes
        text = re.sub(r'♪[^♪]*♪', '', text)
        # Remove leading dashes
        text = re.sub(r'^-\s*', '', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def is_valid_dialogue(self, text: str) -> bool:
        """Check if text is valid dialogue."""
        if len(text) < 3 or len(text) > 500:
            return False
        # Must contain letters
        if not re.search(r'[a-záéíóúñüà]', text, re.IGNORECASE):
            return False
        # Skip full-line annotations
        if re.match(r'^[\[\(♪].*[\]\)♪]$', text):
            return False
        return True

    def merge_from_file(self, filepath: str) -> List[ConversationSegment]:
        """
        Merge subtitles from a single file into conversations.

        Returns list of ConversationSegment with 10-14 lines each.
        """
        subtitles = self.parse_srt(filepath)
        if not subtitles:
            return []

        # Extract film info from filename
        filename = Path(filepath).stem
        parts = filename.rsplit('_', 2)
        film_title = parts[0].replace('_', ' ') if parts else filename

        conversations = []
        current_conv = []
        current_speaker = "A"
        last_end_time = None
        start_time = None

        for sub in subtitles:
            text = self.clean_text(sub.content)
            if not self.is_valid_dialogue(text):
                continue

            # Check if we should start a new conversation
            if last_end_time is not None:
                gap = (sub.start - last_end_time).total_seconds()

                if gap > self.max_gap_seconds or len(current_conv) >= self.max_lines:
                    # Save current conversation if it has enough lines
                    if len(current_conv) >= self.min_lines:
                        conversations.append(self._create_segment(
                            current_conv, film_title, start_time, last_end_time, len(conversations)
                        ))
                    current_conv = []
                    current_speaker = "A"
                    start_time = None
                elif gap > self.speaker_gap_seconds:
                    # Switch speakers
                    current_speaker = "B" if current_speaker == "A" else "A"

            # Add to conversation
            if start_time is None:
                start_time = sub.start

            current_conv.append({
                "speaker": current_speaker,
                "text": text
            })
            last_end_time = sub.end

        # Don't forget last conversation
        if len(current_conv) >= self.min_lines:
            conversations.append(self._create_segment(
                current_conv, film_title, start_time, last_end_time, len(conversations)
            ))

        return conversations

    def _create_segment(
        self,
        conversation: List[Dict],
        film_title: str,
        start_time: timedelta,
        end_time: timedelta,
        index: int
    ) -> ConversationSegment:
        """Create a ConversationSegment from conversation data."""
        return ConversationSegment(
            id=f"{film_title.replace(' ', '_')}_{index:04d}",
            source_film=film_title,
            timestamp_start=self._format_time(start_time),
            timestamp_end=self._format_time(end_time),
            conversation=conversation,
            total_lines=len(conversation),
            duration_seconds=(end_time - start_time).total_seconds()
        )

    @staticmethod
    def _format_time(td: timedelta) -> str:
        """Format timedelta as HH:MM:SS."""
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def merge_from_directory(
        self,
        directory: str,
        show_progress: bool = True
    ) -> List[ConversationSegment]:
        """
        Merge subtitles from all SRT files in a directory.

        Returns list of all ConversationSegments.
        """
        srt_dir = Path(directory)
        srt_files = list(srt_dir.glob("*.srt"))

        logger.info(f"Found {len(srt_files)} SRT files in {directory}")

        all_conversations = []

        if show_progress:
            try:
                from tqdm import tqdm
                files_iter = tqdm(srt_files, desc="Processing SRT files")
            except ImportError:
                files_iter = srt_files
        else:
            files_iter = srt_files

        for srt_file in files_iter:
            conversations = self.merge_from_file(str(srt_file))
            all_conversations.extend(conversations)

        logger.info(f"Created {len(all_conversations)} conversation segments")
        return all_conversations


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def expand_training_dialogues(
    input_file: str,
    output_file: str,
    api_key: Optional[str] = None,
    target_lines: int = 6
) -> int:
    """
    Expand all dialogues for training set using LLM.

    Args:
        input_file: Path to dialogues_by_complexity_cefr.json
        output_file: Path for output JSON
        api_key: Anthropic API key
        target_lines: Target lines per speaker

    Returns:
        Number of dialogues expanded
    """
    # Load dialogues
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Flatten all dialogues
    all_dialogues = []
    for level, dialogues in data.items():
        for d in dialogues:
            d["original_level"] = level
            all_dialogues.append(d)

    logger.info(f"Loaded {len(all_dialogues)} dialogues for expansion")

    # Expand
    expander = DialogueExpander(api_key=api_key)
    expanded = expander.expand_batch(all_dialogues, target_lines_per_speaker=target_lines)

    # Group by simplified level
    by_level = defaultdict(list)
    for d in expanded:
        level = d.get("cefr_simplified", "intermediate")
        by_level[level].append(d)

    # Save
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dict(by_level), f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(expanded)} expanded dialogues to {output_file}")
    return len(expanded)


def merge_eval_dialogues(
    srt_directory: str,
    output_file: str,
    min_lines: int = 10,
    max_lines: int = 16
) -> int:
    """
    Merge subtitles into evaluation dialogues.

    Args:
        srt_directory: Directory containing SRT files
        output_file: Path for output JSON
        min_lines: Minimum lines per conversation
        max_lines: Maximum lines per conversation

    Returns:
        Number of conversations created
    """
    merger = SubtitleMerger(min_lines=min_lines, max_lines=max_lines)
    conversations = merger.merge_from_directory(srt_directory)

    # Convert to dict format
    results = []
    for conv in conversations:
        results.append({
            "id": conv.id,
            "source_film": conv.source_film,
            "timestamp_start": conv.timestamp_start,
            "timestamp_end": conv.timestamp_end,
            "conversation": conv.conversation,
            "total_lines": conv.total_lines,
            "duration_seconds": conv.duration_seconds,
            "cefr_level": None,  # To be classified later
            "scenario": None  # To be classified later
        })

    # Save
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(results)} merged conversations to {output_file}")
    return len(results)


def generate_audio_prompts_v3(
    dialogues_file: str,
    output_dir: str,
    set_type: str = "training"  # or "eval"
):
    """
    Generate V3 audio recording prompts from expanded/merged dialogues.
    """
    with open(dialogues_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Handle different data structures
    if isinstance(data, dict):
        # Grouped by level (training set)
        for level, dialogues in data.items():
            if not dialogues:
                continue

            filename = f"audio_recording_prompts_{level}_v3_{set_type}.md"
            filepath = output_path / filename

            content = generate_prompt_markdown_v3(level, dialogues, set_type)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Generated {filepath}")
    else:
        # List (eval set - needs classification first)
        filename = f"audio_recording_prompts_v3_{set_type}.md"
        filepath = output_path / filename

        content = generate_prompt_markdown_v3("mixed", data, set_type)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Generated {filepath}")


def generate_prompt_markdown_v3(
    level: str,
    dialogues: List[Dict],
    set_type: str
) -> str:
    """Generate markdown content for V3 prompts."""
    level_titles = {
        "beginner": "BEGINNER Level (A1-A2)",
        "intermediate": "INTERMEDIATE Level (B1)",
        "advanced": "ADVANCED Level (B2)",
        "mastery": "MASTERY Level (C1-C2)",
        "mixed": "MIXED Levels"
    }

    lines = [
        f"# Audio Recording Prompts V3 - {level_titles.get(level, level.upper())}",
        f"## Multi-Turn Dialogues ({set_type.title()} Set)",
        "",
        "**Project:** SpeakEasy - Catalan Spanish Language Learning App  ",
        f"**Purpose:** {'Model fine-tuning data' if set_type == 'training' else 'User evaluation ground truth'}  ",
        "**Format:** 5-7 lines per speaker (10-14 total exchanges)",
        "",
        "---",
        "",
        "## Recording Instructions",
        "",
        "1. **Two speakers required** - Record alternating between speakers A and B",
        "2. **Natural pacing** - Leave 0.5-1 second between speaker turns",
        "3. **Match complexity level** - Keep to the specified CEFR level",
        "",
        f"## File Naming: `{{name}}_dialogue_{{number}}_{level}_v3.wav`",
        "",
        "---",
        "",
    ]

    for i, dialogue in enumerate(dialogues[:20], 1):  # Limit to 20 per file
        conv = dialogue.get("conversation", [])
        if not conv:
            continue

        lines.append(f"## Dialogue {i:02d}")
        lines.append(f"**Source:** {dialogue.get('source_film', 'LLM Generated')}")

        if dialogue.get("timestamp_start"):
            lines.append(f"**Timestamp:** {dialogue.get('timestamp_start')} - {dialogue.get('timestamp_end')}")

        if dialogue.get("cefr_level"):
            lines.append(f"**CEFR:** {dialogue.get('cefr_level')}")

        if dialogue.get("scenario"):
            lines.append(f"**Scenario:** {dialogue.get('scenario')}")

        lines.append(f"**Lines:** {len(conv)}")
        lines.append("")
        lines.append("| Speaker | Line |")
        lines.append("|---------|------|")

        for turn in conv:
            speaker = turn.get("speaker", "?")
            text = turn.get("text", "")
            lines.append(f"| {speaker} | \"{text}\" |")

        lines.append("")

        if dialogue.get("catalan_markers"):
            markers = ", ".join(dialogue["catalan_markers"])
            lines.append(f"**Catalan markers:** {markers}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Expand dialogues into multi-turn conversations")
    parser.add_argument(
        "--mode", "-m",
        choices=["expand", "merge", "both"],
        default="both",
        help="Mode: expand (LLM), merge (subtitles), or both"
    )
    parser.add_argument(
        "--input", "-i",
        default="data/eval/dialogues_by_complexity_cefr.json",
        help="Input JSON file for expansion"
    )
    parser.add_argument(
        "--srt-dir", "-s",
        default="data/raw",
        help="Directory with SRT files for merging"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="data/eval",
        help="Output directory"
    )
    parser.add_argument(
        "--prompts-dir", "-p",
        default="data",
        help="Directory for audio prompt markdown files"
    )
    parser.add_argument(
        "--target-lines", "-t",
        type=int,
        default=6,
        help="Target lines per speaker (default: 6)"
    )
    parser.add_argument(
        "--api-key",
        help="Anthropic API key"
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("DIALOGUE EXPANSION PIPELINE")
    print("=" * 60)

    if args.mode in ["expand", "both"]:
        print("\n1. Expanding dialogues with LLM...")
        training_output = str(output_dir / "dialogues_expanded_training.json")
        count = expand_training_dialogues(
            input_file=args.input,
            output_file=training_output,
            api_key=args.api_key,
            target_lines=args.target_lines
        )
        print(f"   Expanded {count} dialogues -> {training_output}")

        print("\n   Generating training audio prompts...")
        generate_audio_prompts_v3(training_output, args.prompts_dir, "training")

    if args.mode in ["merge", "both"]:
        print("\n2. Merging subtitle conversations...")
        eval_output = str(output_dir / "dialogues_merged_eval.json")
        count = merge_eval_dialogues(
            srt_directory=args.srt_dir,
            output_file=eval_output,
            min_lines=10,
            max_lines=16
        )
        print(f"   Merged {count} conversations -> {eval_output}")

        print("\n   Generating eval audio prompts...")
        generate_audio_prompts_v3(eval_output, args.prompts_dir, "eval")

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
