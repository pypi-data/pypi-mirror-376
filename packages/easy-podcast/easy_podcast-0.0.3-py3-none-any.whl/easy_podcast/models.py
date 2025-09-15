"""
Data models for podcast episodes and podcasts.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

from .utils import parse_duration_to_seconds


@dataclass
class Episode:  # pylint: disable=too-many-instance-attributes
    """Represents a single podcast episode.

    Note: audio_file and transcript_file are now computed properties based on
    the episode ID. When accessing the actual file, combine these with the
    podcast's download directory.
    """

    id: str
    published: str
    title: str
    author: str
    duration_seconds: int
    size: int
    audio_link: str
    image: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Episode":
        """Create Episode from dictionary, handling old format conversion."""

        # Remove fields that are now properties
        data = data.copy()
        data.pop("audio_file", None)
        data.pop("transcript_file", None)

        # Handle conversion from old itunes_duration to new duration_seconds
        if "itunes_duration" in data and "duration_seconds" not in data:
            duration_str = data.pop("itunes_duration")
            data["duration_seconds"] = parse_duration_to_seconds(duration_str)

        return cls(**data)

    @property
    def audio_filename(self) -> str:
        """Get the audio filename based on episode ID."""
        return f"{self.id}.mp3"

    @property
    def transcript_filename(self) -> str:
        """Get the transcript filename based on episode ID."""
        return f"{self.id}_transcript.json"

    def to_json(self) -> str:
        """Convert episode to JSON string."""
        return json.dumps(asdict(self))


@dataclass
class Podcast:
    """Represents a podcast, containing its metadata and episodes."""

    title: str
    rss_url: str
    safe_title: str  # Sanitized title used for folder names
    episodes: List[Episode] = field(default_factory=list)
