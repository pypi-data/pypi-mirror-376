"""Manages the creation and writing of cache files.

This module provides a stateless utility class responsible for all
file-writing operations related to caching (e.g., metadata,
transcripts, summaries), ensuring that this logic is centralized
and decoupled from the main application pipeline.

"""
# Copyright 2025 Gabriel Carvalho
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
from dataclasses import asdict
from pathlib import Path

from content_summarizer.data.data_models import VideoMetadata

logger: logging.Logger = logging.getLogger(__name__)


class CacheManager:
    """A stateless utility class for handling cache file operations."""

    def _write_to_file(
        self, content: str, file_path: Path, log_success: bool = True
    ) -> None:
        """Private helper method to write text content to a specified file path.

        This method is the core of the cache writing logic, handling directory
        creation and OS-level errors.

        Args:
            content: The string content to be written to the file.
            file_path: The destination file path.
            log_success: Whether to log a success message.

        Raises:
            OSError: If the file cannot be written due to I/O or permission issues.

        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with file_path.open("w", encoding="utf-8") as f:
                f.write(content)
            if log_success:
                logger.info("File saved successfully to %s", file_path)
        except OSError:
            if log_success:
                logger.exception("Failed to save file")
            raise

    def save_metadata_file(
        self,
        video_metadata: VideoMetadata,
        metadata_file_path: Path,
        log_success: bool = True,
    ) -> None:
        """Serialize VideoMetadata to JSON and saves it to a file.

        Args:
            video_metadata: The dataclass object to be saved.
            metadata_file_path: The destination file path for the metadata.
            log_success: Whether to log a success message.

        """
        video_metadata_dict = asdict(video_metadata)
        json_content = json.dumps(video_metadata_dict, indent=4)

        self._write_to_file(json_content, metadata_file_path, log_success)

    def save_text_file(
        self, text: str, text_file_path: Path, log_success: bool = True
    ) -> None:
        """Save a plain text string to a specified file path.

        Args:
            text: The text content to save.
            text_file_path: The destination file path.
            log_success: Whether to log a success message.

        """
        self._write_to_file(text, text_file_path, log_success)

    def read_keep_cache_flag(self, metadata_path: Path) -> bool:
        """Safely reads the 'keep_cache' flag from the metadata file.

        Args:
            metadata_path: The path to the metadata file.

        Returns:
            True if 'keep_cache' is set to True, False otherwise.

        """
        try:
            with metadata_path.open("r", encoding="utf-8") as f:
                metadata = json.load(f)
                return metadata.get("keep_cache", False)
        except (FileNotFoundError, json.JSONDecodeError):
            return False
