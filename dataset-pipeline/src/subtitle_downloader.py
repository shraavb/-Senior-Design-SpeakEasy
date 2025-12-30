"""
Subtitle Downloader Module
Downloads Spanish subtitles from OpenSubtitles API with focus on Catalan regional content.
"""

import os
import json
import time
import asyncio
import aiohttp
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from ratelimit import limits, sleep_and_retry
from backoff import on_exception, expo
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SubtitleInfo:
    """Metadata for a subtitle file."""
    subtitle_id: str
    film_title: str
    film_year: int
    language: str
    download_url: str
    file_id: str
    fps: float
    upload_date: str
    imdb_id: Optional[str] = None
    genre: Optional[str] = None
    is_catalan_region: bool = False
    catalan_markers_found: List[str] = None

    def __post_init__(self):
        if self.catalan_markers_found is None:
            self.catalan_markers_found = []


class OpenSubtitlesClient:
    """Client for interacting with OpenSubtitles REST API."""

    BASE_URL = "https://api.opensubtitles.com/api/v1"

    def __init__(self, api_key: str, config_path: str = "config/settings.yaml"):
        self.api_key = api_key
        self.session = None
        self.token = None
        self.token_expires = None

        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.headers = {
            "Api-Key": api_key,
            "Content-Type": "application/json",
            "User-Agent": "SpeakEasy-DatasetBuilder/1.0"
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @sleep_and_retry
    @limits(calls=5, period=1)  # Rate limit: 5 calls per second
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """Make a rate-limited request to the API."""
        url = f"{self.BASE_URL}/{endpoint}"

        try:
            async with self.session.request(
                method,
                url,
                json=data,
                params=params
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    logger.error("Authentication failed. Check your API key.")
                    raise AuthenticationError("Invalid API key")
                elif response.status == 429:
                    logger.warning("Rate limited. Waiting...")
                    await asyncio.sleep(5)
                    return await self._make_request(method, endpoint, data, params)
                else:
                    error_text = await response.text()
                    logger.error(f"API error {response.status}: {error_text}")
                    raise APIError(f"API returned {response.status}: {error_text}")
        except aiohttp.ClientError as e:
            logger.error(f"Connection error: {e}")
            raise ConnectionError(f"Failed to connect to API: {e}")

    async def login(self, username: str, password: str) -> str:
        """
        Login to get an authentication token.
        Required for downloading subtitles.
        """
        data = {
            "username": username,
            "password": password
        }

        response = await self._make_request("POST", "login", data=data)
        self.token = response.get("token")
        self.headers["Authorization"] = f"Bearer {self.token}"

        # Update session headers
        if self.session:
            self.session._default_headers.update(self.headers)

        logger.info("Successfully logged in to OpenSubtitles")
        return self.token

    async def search_subtitles(
        self,
        query: Optional[str] = None,
        languages: str = "es",
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        type_filter: str = "movie",
        page: int = 1
    ) -> Dict:
        """
        Search for subtitles matching criteria.

        Args:
            query: Search query (film title, etc.)
            languages: Language code(s), comma-separated
            year_from: Minimum year filter
            year_to: Maximum year filter
            type_filter: 'movie' or 'tvshow'
            page: Page number for pagination
        """
        params = {
            "languages": languages,
            "type": type_filter,
            "page": page
        }

        if query:
            params["query"] = query
        if year_from:
            params["year_from"] = year_from
        if year_to:
            params["year_to"] = year_to

        return await self._make_request("GET", "subtitles", params=params)

    async def search_catalan_regional_content(
        self,
        page: int = 1,
        content_type: str = "movie"
    ) -> List[SubtitleInfo]:
        """
        Search specifically for content likely to have Catalan-accented Spanish.
        """
        subtitles = []
        catalan_keywords = self.config['language']['catalan_keywords']

        # Search using Catalan-related keywords
        for keyword in catalan_keywords:
            try:
                results = await self.search_subtitles(
                    query=keyword,
                    languages="es",
                    year_from=self.config['search_filters']['year_range']['min'],
                    year_to=self.config['search_filters']['year_range']['max'],
                    type_filter=content_type,
                    page=page
                )

                for item in results.get("data", []):
                    subtitle_info = self._parse_subtitle_result(item)
                    if subtitle_info:
                        subtitle_info.is_catalan_region = True
                        subtitles.append(subtitle_info)

                # Respect rate limits
                await asyncio.sleep(0.2)

            except Exception as e:
                logger.warning(f"Error searching for '{keyword}': {e}")
                continue

        # Deduplicate by subtitle_id
        seen_ids = set()
        unique_subtitles = []
        for sub in subtitles:
            if sub.subtitle_id not in seen_ids:
                seen_ids.add(sub.subtitle_id)
                unique_subtitles.append(sub)

        logger.info(f"Found {len(unique_subtitles)} unique Catalan-regional subtitles")
        return unique_subtitles

    def _parse_subtitle_result(self, item: Dict) -> Optional[SubtitleInfo]:
        """Parse a subtitle search result into SubtitleInfo."""
        try:
            attributes = item.get("attributes", {})
            feature_details = attributes.get("feature_details", {})

            # Get file info (first file)
            files = attributes.get("files", [])
            if not files:
                return None

            file_info = files[0]

            return SubtitleInfo(
                subtitle_id=str(item.get("id", "")),
                film_title=feature_details.get("title", "Unknown"),
                film_year=feature_details.get("year", 0),
                language=attributes.get("language", "es"),
                download_url="",  # Will be fetched separately
                file_id=str(file_info.get("file_id", "")),
                fps=attributes.get("fps", 0.0),
                upload_date=attributes.get("upload_date", ""),
                imdb_id=feature_details.get("imdb_id"),
                genre=feature_details.get("genres", [""])[0] if feature_details.get("genres") else None
            )
        except Exception as e:
            logger.warning(f"Failed to parse subtitle result: {e}")
            return None

    async def get_download_link(self, file_id: str) -> str:
        """
        Get a download link for a subtitle file.
        Requires authentication.
        """
        data = {"file_id": int(file_id)}
        response = await self._make_request("POST", "download", data=data)
        return response.get("link", "")

    async def download_subtitle(
        self,
        subtitle_info: SubtitleInfo,
        output_dir: str = "data/raw"
    ) -> Optional[str]:
        """
        Download a subtitle file to disk.

        Returns the path to the downloaded file, or None if failed.
        """
        try:
            # Get download link
            download_url = await self.get_download_link(subtitle_info.file_id)
            if not download_url:
                logger.warning(f"No download URL for {subtitle_info.film_title}")
                return None

            # Download the file
            async with self.session.get(download_url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to download {subtitle_info.film_title}")
                    return None

                content = await response.read()

            # Create output path
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Create safe filename
            safe_title = "".join(c for c in subtitle_info.film_title if c.isalnum() or c in " -_")
            filename = f"{safe_title}_{subtitle_info.film_year}_{subtitle_info.subtitle_id}.srt"
            filepath = output_path / filename

            # Write file
            with open(filepath, "wb") as f:
                f.write(content)

            logger.info(f"Downloaded: {filename}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error downloading {subtitle_info.film_title}: {e}")
            return None

    async def batch_download(
        self,
        subtitles: List[SubtitleInfo],
        output_dir: str = "data/raw",
        max_concurrent: int = 3
    ) -> List[str]:
        """
        Download multiple subtitles with concurrency control.
        """
        downloaded_paths = []
        semaphore = asyncio.Semaphore(max_concurrent)

        async def download_with_semaphore(sub: SubtitleInfo) -> Optional[str]:
            async with semaphore:
                path = await self.download_subtitle(sub, output_dir)
                await asyncio.sleep(0.5)  # Rate limiting
                return path

        tasks = [download_with_semaphore(sub) for sub in subtitles]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, str) and result:
                downloaded_paths.append(result)

        logger.info(f"Successfully downloaded {len(downloaded_paths)}/{len(subtitles)} subtitles")
        return downloaded_paths

    def save_metadata(
        self,
        subtitles: List[SubtitleInfo],
        output_path: str = "data/raw/metadata.json"
    ):
        """Save subtitle metadata to JSON for reference."""
        metadata = [asdict(sub) for sub in subtitles]

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved metadata for {len(subtitles)} subtitles to {output_path}")


class AuthenticationError(Exception):
    """Raised when API authentication fails."""
    pass


class APIError(Exception):
    """Raised when API returns an error."""
    pass


# Alternative: OPUS Corpus Downloader
class OPUSCorpusDownloader:
    """
    Download Catalan/Spanish subtitles from OPUS corpus.
    This is a more research-friendly alternative to OpenSubtitles API.
    """

    OPUS_URL = "https://opus.nlpl.eu/download.php"

    def __init__(self, output_dir: str = "data/raw/opus"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download_opensubtitles_corpus(
        self,
        source_lang: str = "ca",  # Catalan
        target_lang: str = "es",  # Spanish
        version: str = "v2018"
    ) -> str:
        """
        Download the OpenSubtitles parallel corpus from OPUS.

        This contains aligned Catalan-Spanish subtitle pairs,
        useful for understanding regional variations.
        """
        # OPUS download URL format
        url = f"https://opus.nlpl.eu/download.php?f=OpenSubtitles/{version}/moses/{source_lang}-{target_lang}.txt.zip"

        output_file = self.output_dir / f"OpenSubtitles_{source_lang}_{target_lang}.zip"

        logger.info(f"Downloading OPUS corpus: {source_lang}-{target_lang}")

        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Downloaded to {output_file}")
            return str(output_file)
        else:
            logger.error(f"Failed to download corpus: {response.status_code}")
            return ""

    def download_spanish_monolingual(self, version: str = "v2018") -> str:
        """Download Spanish monolingual subtitle corpus."""
        url = f"https://opus.nlpl.eu/download.php?f=OpenSubtitles/{version}/mono/es.txt.gz"

        output_file = self.output_dir / "OpenSubtitles_es_mono.txt.gz"

        logger.info("Downloading Spanish monolingual corpus")

        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Downloaded to {output_file}")
            return str(output_file)
        else:
            logger.error(f"Failed to download: {response.status_code}")
            return ""


async def main():
    """Example usage of the subtitle downloader."""

    # Load API key from environment
    api_key = os.getenv("OPENSUBTITLES_API_KEY")
    if not api_key:
        print("Please set OPENSUBTITLES_API_KEY environment variable")
        print("Get your API key from: https://www.opensubtitles.com/en/consumers")
        return

    async with OpenSubtitlesClient(api_key) as client:
        # Optional: Login for download access
        username = os.getenv("OPENSUBTITLES_USERNAME")
        password = os.getenv("OPENSUBTITLES_PASSWORD")

        if username and password:
            await client.login(username, password)

        # Search for Catalan-regional content
        print("\nSearching for Catalan-regional Spanish subtitles...")
        subtitles = await client.search_catalan_regional_content(
            page=1,
            content_type="movie"
        )

        print(f"\nFound {len(subtitles)} subtitles:")
        for sub in subtitles[:10]:  # Show first 10
            print(f"  - {sub.film_title} ({sub.film_year})")

        # Save metadata
        client.save_metadata(subtitles)

        # Download subtitles (if logged in)
        if client.token:
            print("\nDownloading subtitles...")
            downloaded = await client.batch_download(subtitles[:5])  # Limit for demo
            print(f"Downloaded {len(downloaded)} files")


if __name__ == "__main__":
    asyncio.run(main())
