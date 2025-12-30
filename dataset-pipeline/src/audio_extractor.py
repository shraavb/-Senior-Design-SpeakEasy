#!/usr/bin/env python3
"""
Audio Extractor for Ground Truth Dataset

Extracts audio clips from movies/videos using subtitle timestamps.
Requires FFmpeg to be installed: brew install ffmpeg

Usage:
    python src/audio_extractor.py --video path/to/movie.mp4 --subtitle path/to/movie.srt --output data/audio/
    python src/audio_extractor.py --video-dir movies/ --output data/audio/
"""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional
import hashlib


@dataclass
class SubtitleEntry:
    """Represents a single subtitle entry with timestamp and text."""
    index: int
    start_time: str  # HH:MM:SS,mmm format
    end_time: str
    text: str
    start_seconds: float
    end_seconds: float


@dataclass
class AudioClip:
    """Metadata for an extracted audio clip."""
    clip_id: str
    source_video: str
    source_subtitle: str
    subtitle_index: int
    start_time: str
    end_time: str
    duration_seconds: float
    text: str
    audio_file: str
    scenario: Optional[str] = None


def check_ffmpeg():
    """Check if FFmpeg is installed."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def time_to_seconds(time_str: str) -> float:
    """Convert SRT timestamp (HH:MM:SS,mmm) to seconds."""
    # Handle both comma and period as decimal separator
    time_str = time_str.replace(',', '.')
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def seconds_to_ffmpeg_time(seconds: float) -> str:
    """Convert seconds to FFmpeg time format (HH:MM:SS.mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def parse_srt(srt_path: str) -> List[SubtitleEntry]:
    """Parse an SRT file and return list of subtitle entries."""
    entries = []

    with open(srt_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Split by double newline (subtitle blocks)
    blocks = re.split(r'\n\s*\n', content.strip())

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue

        try:
            # First line is index
            index = int(lines[0].strip())

            # Second line is timestamp
            timestamp_match = re.match(
                r'(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})',
                lines[1].strip()
            )
            if not timestamp_match:
                continue

            start_time = timestamp_match.group(1)
            end_time = timestamp_match.group(2)

            # Remaining lines are text
            text = ' '.join(lines[2:]).strip()
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', text)

            if text:
                entries.append(SubtitleEntry(
                    index=index,
                    start_time=start_time,
                    end_time=end_time,
                    text=text,
                    start_seconds=time_to_seconds(start_time),
                    end_seconds=time_to_seconds(end_time),
                ))
        except (ValueError, IndexError):
            continue

    return entries


def extract_audio_clip(
    video_path: str,
    start_seconds: float,
    end_seconds: float,
    output_path: str,
    padding: float = 0.2,
    audio_format: str = "wav"
) -> bool:
    """
    Extract an audio clip from a video file using FFmpeg.

    Args:
        video_path: Path to source video
        start_seconds: Start time in seconds
        end_seconds: End time in seconds
        output_path: Path for output audio file
        padding: Extra seconds to add before/after (for context)
        audio_format: Output format (wav, mp3, flac)

    Returns:
        True if successful, False otherwise
    """
    # Add padding
    start = max(0, start_seconds - padding)
    duration = (end_seconds - start_seconds) + (2 * padding)

    # FFmpeg command
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output
        "-i", video_path,
        "-ss", seconds_to_ffmpeg_time(start),
        "-t", str(duration),
        "-vn",  # No video
        "-acodec", "pcm_s16le" if audio_format == "wav" else "libmp3lame",
        "-ar", "16000",  # 16kHz sample rate (good for speech)
        "-ac", "1",  # Mono
        "-loglevel", "error",
        output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return False


def find_matching_video(subtitle_path: str, video_dir: str) -> Optional[str]:
    """
    Try to find a video file that matches the subtitle file.
    Matches by similar filename.
    """
    srt_name = Path(subtitle_path).stem
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.m4v', '.webm']

    video_path = Path(video_dir)

    # Try exact match first
    for ext in video_extensions:
        candidate = video_path / f"{srt_name}{ext}"
        if candidate.exists():
            return str(candidate)

    # Try partial match (movie name without year/ID)
    # e.g., "A Gun in Each Hand_2012_889263.srt" -> "A Gun in Each Hand"
    base_name = re.split(r'_\d{4}', srt_name)[0]

    for video_file in video_path.iterdir():
        if video_file.suffix.lower() in video_extensions:
            if base_name.lower() in video_file.stem.lower():
                return str(video_file)

    return None


def extract_from_subtitle(
    subtitle_path: str,
    video_path: str,
    output_dir: str,
    max_clips: Optional[int] = None,
    min_duration: float = 0.5,
    max_duration: float = 10.0,
    audio_format: str = "wav"
) -> List[AudioClip]:
    """
    Extract audio clips from a video using subtitle timestamps.

    Args:
        subtitle_path: Path to SRT file
        video_path: Path to video file
        output_dir: Directory for output audio files
        max_clips: Maximum number of clips to extract (None for all)
        min_duration: Minimum clip duration in seconds
        max_duration: Maximum clip duration in seconds
        audio_format: Output audio format

    Returns:
        List of AudioClip metadata objects
    """
    # Parse subtitles
    entries = parse_srt(subtitle_path)
    print(f"Found {len(entries)} subtitle entries in {Path(subtitle_path).name}")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Create subdirectory for this video
    video_name = Path(video_path).stem
    video_output = output_path / video_name
    video_output.mkdir(exist_ok=True)

    clips = []
    extracted = 0

    for entry in entries:
        # Check duration constraints
        duration = entry.end_seconds - entry.start_seconds
        if duration < min_duration or duration > max_duration:
            continue

        # Generate clip ID
        clip_id = hashlib.md5(
            f"{video_name}_{entry.index}_{entry.text}".encode()
        ).hexdigest()[:12]

        # Output filename
        audio_filename = f"{clip_id}_{entry.index:04d}.{audio_format}"
        audio_path = video_output / audio_filename

        # Extract audio
        success = extract_audio_clip(
            video_path,
            entry.start_seconds,
            entry.end_seconds,
            str(audio_path),
            audio_format=audio_format
        )

        if success:
            clip = AudioClip(
                clip_id=clip_id,
                source_video=video_name,
                source_subtitle=Path(subtitle_path).name,
                subtitle_index=entry.index,
                start_time=entry.start_time,
                end_time=entry.end_time,
                duration_seconds=duration,
                text=entry.text,
                audio_file=str(audio_path.relative_to(output_path)),
            )
            clips.append(clip)
            extracted += 1

            if extracted % 50 == 0:
                print(f"  Extracted {extracted} clips...")

            if max_clips and extracted >= max_clips:
                break

    print(f"Successfully extracted {extracted} audio clips")
    return clips


def main():
    parser = argparse.ArgumentParser(
        description="Extract audio clips from videos using subtitle timestamps"
    )
    parser.add_argument(
        "--video",
        type=str,
        help="Path to video file",
    )
    parser.add_argument(
        "--subtitle",
        type=str,
        help="Path to SRT subtitle file",
    )
    parser.add_argument(
        "--video-dir",
        type=str,
        help="Directory containing video files (auto-matches with subtitles)",
    )
    parser.add_argument(
        "--subtitle-dir",
        type=str,
        default="data/raw",
        help="Directory containing subtitle files",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/audio",
        help="Output directory for audio clips",
    )
    parser.add_argument(
        "--max-clips",
        type=int,
        default=None,
        help="Maximum clips per video (default: all)",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="wav",
        choices=["wav", "mp3", "flac"],
        help="Output audio format",
    )
    parser.add_argument(
        "--list-subtitles",
        action="store_true",
        help="List available subtitle files and exit",
    )
    args = parser.parse_args()

    # Check FFmpeg
    if not check_ffmpeg():
        print("Error: FFmpeg is not installed.")
        print("Install with: brew install ffmpeg")
        return

    # List subtitles mode
    if args.list_subtitles:
        srt_dir = Path(args.subtitle_dir)
        if srt_dir.exists():
            srt_files = list(srt_dir.glob("*.srt"))
            print(f"\nFound {len(srt_files)} subtitle files in {args.subtitle_dir}:\n")
            for srt in sorted(srt_files)[:20]:
                print(f"  - {srt.name}")
            if len(srt_files) > 20:
                print(f"  ... and {len(srt_files) - 20} more")
        return

    all_clips = []

    # Single video + subtitle mode
    if args.video and args.subtitle:
        if not Path(args.video).exists():
            print(f"Error: Video file not found: {args.video}")
            return
        if not Path(args.subtitle).exists():
            print(f"Error: Subtitle file not found: {args.subtitle}")
            return

        print(f"\nExtracting audio from: {args.video}")
        clips = extract_from_subtitle(
            args.subtitle,
            args.video,
            args.output,
            max_clips=args.max_clips,
            audio_format=args.format,
        )
        all_clips.extend(clips)

    # Batch mode: match videos with subtitles
    elif args.video_dir:
        if not Path(args.video_dir).exists():
            print(f"Error: Video directory not found: {args.video_dir}")
            return

        srt_dir = Path(args.subtitle_dir)
        srt_files = list(srt_dir.glob("*.srt"))

        print(f"\nLooking for video matches for {len(srt_files)} subtitles...")

        matched = 0
        for srt_file in srt_files:
            video_path = find_matching_video(str(srt_file), args.video_dir)
            if video_path:
                print(f"\n{'='*60}")
                print(f"Matched: {srt_file.name}")
                print(f"  Video: {Path(video_path).name}")
                print(f"{'='*60}")

                clips = extract_from_subtitle(
                    str(srt_file),
                    video_path,
                    args.output,
                    max_clips=args.max_clips,
                    audio_format=args.format,
                )
                all_clips.extend(clips)
                matched += 1

        print(f"\nMatched {matched} videos with subtitles")

    else:
        print("Error: Provide either --video and --subtitle, or --video-dir")
        print("\nExamples:")
        print("  python src/audio_extractor.py --video movie.mp4 --subtitle movie.srt")
        print("  python src/audio_extractor.py --video-dir /path/to/movies/")
        print("  python src/audio_extractor.py --list-subtitles")
        return

    # Save metadata
    if all_clips:
        output_path = Path(args.output)
        metadata_file = output_path / "audio_clips_metadata.json"

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(
                [asdict(clip) for clip in all_clips],
                f,
                indent=2,
                ensure_ascii=False
            )

        print(f"\n{'='*60}")
        print(f"EXTRACTION COMPLETE")
        print(f"{'='*60}")
        print(f"Total clips extracted: {len(all_clips)}")
        print(f"Output directory: {args.output}")
        print(f"Metadata saved to: {metadata_file}")

        # Summary by video
        videos = {}
        for clip in all_clips:
            videos[clip.source_video] = videos.get(clip.source_video, 0) + 1

        print(f"\nClips per video:")
        for video, count in sorted(videos.items()):
            print(f"  {video}: {count} clips")


if __name__ == "__main__":
    main()
