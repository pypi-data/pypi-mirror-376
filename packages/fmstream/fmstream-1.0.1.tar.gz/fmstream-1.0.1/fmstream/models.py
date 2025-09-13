"""
Data models for FM Stream library
"""

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class AudioStream:
    """Represents an audio stream for a radio station"""
    title: str
    url: str
    extra: str = ""
    
    def __post_init__(self):
        """Ensure URL has proper protocol"""
        if self.url and not self.url.startswith(("http://", "https://")):
            self.url = "http://" + self.url


@dataclass
class StreamGroup:
    """Represents a group of audio streams"""
    group_index: int
    group_name: str
    group_name_norm: str
    streams: List[AudioStream]


@dataclass
class RadioStation:
    """Represents a complete radio station with metadata and streams"""
    id: int
    title: str
    location: str = ""
    country_code: str = ""
    genre: str = ""
    language: str = ""
    frequency: str = ""
    link: str = ""
    short_desc: str = ""
    long_desc: str = ""
    streams: List[AudioStream] = None
    
    def __post_init__(self):
        if self.streams is None:
            self.streams = []
