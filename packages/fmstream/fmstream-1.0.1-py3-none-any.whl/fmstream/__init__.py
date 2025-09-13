"""
FMStream Library - A Python library for scraping FM radio station data from fmstream.org

This library provides functionality to:
- Extract FM radio station information
- Parse audio stream URLs
- Match stations with their corresponding streams
- Return structured data for radio stations
- Serve data via FastAPI REST API
"""

from .scraper import FMStreamScraper
from .models import RadioStation, AudioStream, StreamGroup
from .api import app as fastapi_app

__version__ = "1.0.0"
__author__ = "HaoWasabi"
__email__ = "truonggiahao24@example.com"

__all__ = ["FMStreamScraper", "RadioStation", "AudioStream", "StreamGroup", "fastapi_app"]
