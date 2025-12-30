#!/usr/bin/env python3
"""
Catalan-Accented Spanish Dataset Pipeline
Main entry point for building fine-tuning datasets from movie subtitles.

Usage:
    python main.py download    # Download subtitles from OpenSubtitles
    python main.py extract     # Extract dialogs from downloaded SRT files
    python main.py classify    # Classify dialogs into scenarios
    python main.py format      # Format into JSONL/CSV for training
    python main.py all         # Run full pipeline
"""

import os
import sys
import asyncio
import click
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from subtitle_downloader import OpenSubtitlesClient, OPUSCorpusDownloader
from dialog_extractor import batch_extract_dialogs, SubtitleParser
from scenario_classifier import classify_dialogs, print_classification_report
from dataset_formatter import process_dataset

console = Console()

# Default paths
DEFAULT_CONFIG = "config/settings.yaml"
RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed"
EVAL_DATA_DIR = "data/eval"


@click.group()
@click.option('--config', '-c', default=DEFAULT_CONFIG, help='Path to config file')
@click.pass_context
def cli(ctx, config):
    """Catalan-Accented Spanish Dataset Builder"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = config


@cli.command()
@click.option('--method', '-m', type=click.Choice(['api', 'opus']), default='api',
              help='Download method: api (OpenSubtitles API) or opus (OPUS corpus)')
@click.option('--max-subtitles', '-n', default=100, help='Maximum number of subtitles to download')
@click.pass_context
def download(ctx, method, max_subtitles):
    """Download Spanish subtitles from selected source."""
    config = ctx.obj['config']

    console.print(Panel.fit(
        "[bold blue]Subtitle Downloader[/bold blue]\n"
        f"Method: {method}\n"
        f"Max subtitles: {max_subtitles}",
        title="🎬 Download"
    ))

    if method == 'api':
        # Check for API key
        api_key = os.getenv("OPENSUBTITLES_API_KEY")
        if not api_key:
            console.print("[red]Error:[/red] OPENSUBTITLES_API_KEY not set")
            console.print("\nTo get an API key:")
            console.print("1. Go to https://www.opensubtitles.com/en/consumers")
            console.print("2. Create a free account")
            console.print("3. Generate an API key")
            console.print("4. Set it: export OPENSUBTITLES_API_KEY=your_key")
            return

        asyncio.run(_download_from_api(api_key, config, max_subtitles))

    elif method == 'opus':
        _download_from_opus()


async def _download_from_api(api_key: str, config: str, max_subtitles: int):
    """Download using OpenSubtitles API."""
    async with OpenSubtitlesClient(api_key, config) as client:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Search for Catalan-regional content
            task = progress.add_task("Searching for Catalan-regional content...", total=None)

            subtitles = []
            for page in range(1, 4):  # Search first 3 pages
                results = await client.search_catalan_regional_content(
                    page=page,
                    content_type="movie"
                )
                subtitles.extend(results)

                if len(subtitles) >= max_subtitles:
                    break

            subtitles = subtitles[:max_subtitles]
            progress.update(task, description=f"Found {len(subtitles)} subtitles")

            # Try to login for downloading
            username = os.getenv("OPENSUBTITLES_USERNAME")
            password = os.getenv("OPENSUBTITLES_PASSWORD")

            if username and password:
                progress.update(task, description="Logging in...")
                await client.login(username, password)

                progress.update(task, description="Downloading subtitles...")
                downloaded = await client.batch_download(subtitles, RAW_DATA_DIR)

                console.print(f"\n✅ Downloaded {len(downloaded)} subtitle files to {RAW_DATA_DIR}")
            else:
                console.print("\n[yellow]Note:[/yellow] Set OPENSUBTITLES_USERNAME and PASSWORD to download files")
                console.print("Saving metadata only...")

            # Save metadata
            client.save_metadata(subtitles, f"{RAW_DATA_DIR}/metadata.json")

    # Print results
    _print_download_summary(subtitles)


def _download_from_opus():
    """Download from OPUS corpus."""
    downloader = OPUSCorpusDownloader(f"{RAW_DATA_DIR}/opus")

    console.print("Downloading OPUS OpenSubtitles corpus...")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        # Download Catalan-Spanish parallel corpus
        task = progress.add_task("Downloading Catalan-Spanish corpus...", total=None)
        ca_es_path = downloader.download_opensubtitles_corpus("ca", "es")

        # Download Spanish monolingual
        progress.update(task, description="Downloading Spanish monolingual corpus...")
        es_path = downloader.download_spanish_monolingual()

    console.print(f"\n✅ Downloaded OPUS data:")
    if ca_es_path:
        console.print(f"  - Catalan-Spanish: {ca_es_path}")
    if es_path:
        console.print(f"  - Spanish mono: {es_path}")


def _print_download_summary(subtitles):
    """Print a summary table of downloaded subtitles."""
    if not subtitles:
        return

    table = Table(title="Downloaded Subtitles")
    table.add_column("Title", style="cyan")
    table.add_column("Year", style="magenta")
    table.add_column("Genre", style="green")

    for sub in subtitles[:20]:  # Show first 20
        table.add_row(
            sub.film_title[:40],
            str(sub.film_year),
            sub.genre or "N/A"
        )

    if len(subtitles) > 20:
        table.add_row("...", f"+{len(subtitles)-20} more", "")

    console.print(table)


@cli.command()
@click.option('--input-dir', '-i', default=RAW_DATA_DIR, help='Directory with SRT files')
@click.option('--output', '-o', default=f'{PROCESSED_DATA_DIR}/all_dialogs.json',
              help='Output JSON file')
@click.pass_context
def extract(ctx, input_dir, output):
    """Extract dialogs from downloaded SRT files."""
    config = ctx.obj['config']

    console.print(Panel.fit(
        f"[bold blue]Dialog Extractor[/bold blue]\n"
        f"Input: {input_dir}\n"
        f"Output: {output}",
        title="📝 Extract"
    ))

    # Check for SRT files
    srt_files = list(Path(input_dir).glob("*.srt"))
    if not srt_files:
        console.print(f"[yellow]No SRT files found in {input_dir}[/yellow]")
        console.print("Run 'python main.py download' first")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"Extracting from {len(srt_files)} files...", total=None)

        dialogs = batch_extract_dialogs(input_dir, output, config)

        progress.update(task, description="Done!")

    console.print(f"\n✅ Extracted {len(dialogs)} dialogs to {output}")

    # Show sample
    if dialogs:
        console.print("\n[bold]Sample dialogs:[/bold]")
        for d in dialogs[:3]:
            console.print(f"  [{d.start_timestamp}] {d.text[:60]}...")


@cli.command()
@click.option('--input', '-i', default=f'{PROCESSED_DATA_DIR}/all_dialogs.json',
              help='Input dialogs JSON')
@click.option('--output', '-o', default=f'{PROCESSED_DATA_DIR}/classified_dialogs.json',
              help='Output classified JSON')
@click.option('--semantic/--no-semantic', default=True,
              help='Use semantic classification (requires sentence-transformers)')
@click.pass_context
def classify(ctx, input, output, semantic):
    """Classify dialogs into Personal & Social scenarios."""
    config = ctx.obj['config']

    console.print(Panel.fit(
        f"[bold blue]Scenario Classifier[/bold blue]\n"
        f"Input: {input}\n"
        f"Output: {output}\n"
        f"Semantic: {semantic}",
        title="🏷️ Classify"
    ))

    if not Path(input).exists():
        console.print(f"[red]Error:[/red] {input} not found")
        console.print("Run 'python main.py extract' first")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Classifying dialogs...", total=None)

        counts = classify_dialogs(input, output, config, semantic)

        progress.update(task, description="Done!")

    console.print(f"\n✅ Classified dialogs saved to {output}")
    print_classification_report(counts)


@cli.command()
@click.option('--input', '-i', default=f'{PROCESSED_DATA_DIR}/classified_dialogs.json',
              help='Input classified dialogs')
@click.option('--output-dir', '-o', default=PROCESSED_DATA_DIR,
              help='Output directory for datasets')
@click.pass_context
def format(ctx, input, output_dir):
    """Format classified dialogs into JSONL/CSV for fine-tuning."""
    config = ctx.obj['config']

    console.print(Panel.fit(
        f"[bold blue]Dataset Formatter[/bold blue]\n"
        f"Input: {input}\n"
        f"Output: {output_dir}",
        title="📦 Format"
    ))

    if not Path(input).exists():
        console.print(f"[red]Error:[/red] {input} not found")
        console.print("Run 'python main.py classify' first")
        return

    process_dataset(input, output_dir, config)

    console.print("\n✅ Datasets ready for fine-tuning!")


@cli.command()
@click.option('--max-subtitles', '-n', default=50, help='Maximum subtitles to download')
@click.pass_context
def all(ctx, max_subtitles):
    """Run the full pipeline: download → extract → classify → format."""
    config = ctx.obj['config']

    console.print(Panel.fit(
        "[bold green]Full Pipeline[/bold green]\n"
        "download → extract → classify → format",
        title="🚀 Complete Pipeline"
    ))

    # Check for API key
    api_key = os.getenv("OPENSUBTITLES_API_KEY")
    if not api_key:
        console.print("[yellow]Warning:[/yellow] No API key set, using demo mode with OPUS corpus")
        ctx.invoke(download, method='opus')
    else:
        ctx.invoke(download, method='api', max_subtitles=max_subtitles)

    # Continue with pipeline
    ctx.invoke(extract)
    ctx.invoke(classify)
    ctx.invoke(format)

    console.print(Panel.fit(
        "[bold green]Pipeline Complete![/bold green]\n\n"
        "Generated files:\n"
        f"  📄 {PROCESSED_DATA_DIR}/train_catalan_spanish.jsonl\n"
        f"  📄 {PROCESSED_DATA_DIR}/eval_catalan_spanish.jsonl\n"
        f"  📊 {PROCESSED_DATA_DIR}/catalan_spanish_full.csv\n"
        f"  🧪 {PROCESSED_DATA_DIR}/eval_prompts.json",
        title="✅ Done"
    ))


@cli.command()
def status():
    """Show current pipeline status and file counts."""
    console.print(Panel.fit("[bold]Pipeline Status[/bold]", title="📊 Status"))

    # Check directories
    dirs = {
        "Raw data": RAW_DATA_DIR,
        "Processed": PROCESSED_DATA_DIR,
    }

    table = Table()
    table.add_column("Location", style="cyan")
    table.add_column("Files", style="magenta")
    table.add_column("Status", style="green")

    for name, dir_path in dirs.items():
        path = Path(dir_path)
        if path.exists():
            files = list(path.glob("*"))
            file_count = len(files)
            status = "✅ Ready" if file_count > 0 else "⚠️ Empty"
        else:
            file_count = 0
            status = "❌ Missing"

        table.add_row(name, str(file_count), status)

    console.print(table)

    # Check specific files
    console.print("\n[bold]Key Files:[/bold]")
    key_files = [
        (f"{RAW_DATA_DIR}/metadata.json", "Subtitle metadata"),
        (f"{PROCESSED_DATA_DIR}/all_dialogs.json", "Extracted dialogs"),
        (f"{PROCESSED_DATA_DIR}/classified_dialogs.json", "Classified dialogs"),
        (f"{PROCESSED_DATA_DIR}/train_catalan_spanish.jsonl", "Training dataset"),
        (f"{PROCESSED_DATA_DIR}/eval_catalan_spanish.jsonl", "Evaluation dataset"),
    ]

    for filepath, description in key_files:
        exists = Path(filepath).exists()
        icon = "✅" if exists else "❌"
        console.print(f"  {icon} {description}: {filepath}")


if __name__ == "__main__":
    cli()
