"""
Main scraper class for extracting FM radio station data
"""

import requests
import re
import json
import unicodedata
import urllib.parse
from bs4 import BeautifulSoup
import difflib
from typing import List, Dict, Any, Optional

from .models import RadioStation, AudioStream, StreamGroup


class FMStreamScraper:
    """
    A scraper for extracting FM radio station data from fmstream.org
    
    This class provides methods to:
    - Extract station information from HTML pages
    - Parse JavaScript data for audio streams
    - Match stations with their corresponding streams
    """
    
    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Normalize text for comparison by removing accents, converting to lowercase
        
        Args:
            text: Input text to normalize
            
        Returns:
            Normalized text string
        """
        if not text:
            return ""
        
        text = str(text).lower().strip()
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(ch for ch in text if not unicodedata.combining(ch))
        return text

    @classmethod
    def extract_station_info(cls, url: str) -> List[Dict[str, str]]:
        """
        Extract FM radio station information from fmstream.org page
        
        Args:
            url: URL of the fmstream.org page to scrape
            
        Returns:
            List of dictionaries containing station information
            
        Raises:
            requests.RequestException: If the HTTP request fails
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to fetch URL {url}: {e}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        stations = []

        for block in soup.select("div.stnblock"):
            title = block.select_one("h3.stn")
            location = block.select_one("span.loc")
            style = block.select_one("span.sty")
            freqs = block.select("span.frq")
            link = block.select_one("a.hp")
            slogan = block.select_one("span.slo")
            desc = block.select_one("span.desc")

            # Extract country code from location
            loc_text = location.get_text(strip=True) if location else ""
            country_code = loc_text[:3].upper() if loc_text else ""

            # Extract language from style
            style_text = style.get_text(strip=True) if style else ""
            language = ""
            if style_text:
                for lang in ["vietnamese", "english", "french", "khmer", "chinese", "thai"]:
                    if lang in style_text.lower():
                        language = lang
                        break

            station = {
                "title": title.get_text(strip=True) if title else "",
                "location": loc_text,
                "country_code": country_code,
                "genre": style_text,
                "language": language,
                "frequency": " | ".join(f.get_text(strip=True) for f in freqs) if freqs else "",
                "link": link["href"] if link else "",
                "short_desc": slogan.get_text(strip=True) if slogan else "",
                "long_desc": desc.get_text(strip=True) if desc else "",
            }
            stations.append(station)

        return stations

    @classmethod
    def extract_audio_streams(cls, url: str) -> List[StreamGroup]:
        """
        Extract audio stream data from JavaScript on fmstream.org page
        
        Args:
            url: URL of the fmstream.org page to scrape
            
        Returns:
            List of StreamGroup objects containing organized stream data
            
        Raises:
            requests.RequestException: If the HTTP request fails
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            html = response.text
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to fetch URL {url}: {e}")

        # Extract JavaScript data array
        match = re.search(r"var\s+data\s*=\s*(\[.*?\]);", html, re.S)
        if not match:
            return []

        # Clean up JavaScript array format
        arr_text = match.group(1)
        arr_text = arr_text.replace("\\/", "/")
        arr_text = re.sub(r",\s*,", ", null,", arr_text)
        arr_text = arr_text.replace(",,", ", null,")
        arr_text = re.sub(r"'([^']*)'", r'"\1"', arr_text)

        try:
            data = json.loads(arr_text)
        except json.JSONDecodeError:
            return []

        groups = []
        for group_index, group in enumerate(data):
            if not isinstance(group, list):
                continue
                
            streams = []
            group_name = ""
            
            for item in group:
                if not isinstance(item, list):
                    continue
                    
                url_field = item[0] if len(item) > 0 else ""
                title_field = item[1] if len(item) > 1 else ""
                extra_field = item[2] if len(item) > 2 else ""

                url_str = str(url_field).strip() if url_field is not None else ""
                title_str = str(title_field).strip() if title_field is not None else ""
                extra_str = str(extra_field).strip() if extra_field is not None else ""

                if url_str:
                    stream = AudioStream(
                        title=title_str,
                        url=url_str,
                        extra=extra_str
                    )
                    streams.append(stream)
                    
                    if not group_name and title_str:
                        group_name = title_str

            # Fallback group name generation
            if not group_name:
                for stream in streams:
                    if stream.extra:
                        group_name = stream.extra
                        break
                        
                if not group_name and streams:
                    try:
                        parsed_url = urllib.parse.urlparse(streams[0].url)
                        group_name = parsed_url.hostname or ""
                    except Exception:
                        group_name = ""

            stream_group = StreamGroup(
                group_index=group_index,
                group_name=group_name,
                group_name_norm=cls._normalize_text(group_name),
                streams=streams
            )
            groups.append(stream_group)

        return groups

    @classmethod
    def match_station_to_group(cls, station_title: str, groups: List[StreamGroup]) -> Optional[StreamGroup]:
        """
        Match a radio station to its corresponding stream group using fuzzy matching
        
        Args:
            station_title: Title of the radio station
            groups: List of available stream groups
            
        Returns:
            Best matching StreamGroup or None if no match found
        """
        station_norm = cls._normalize_text(station_title)
        if not groups or not station_norm:
            return None

        # 1. Direct group name containment
        for group in groups:
            group_norm = group.group_name_norm
            if group_norm and (group_norm in station_norm or station_norm in group_norm):
                return group

        # 2. Stream title/extra containment
        for group in groups:
            for stream in group.streams:
                title_norm = cls._normalize_text(stream.title)
                extra_norm = cls._normalize_text(stream.extra)
                
                if title_norm and (title_norm in station_norm or station_norm in title_norm):
                    return group
                if extra_norm and (extra_norm in station_norm or station_norm in extra_norm):
                    return group

        # 3. Fuzzy match on group names
        group_names = [g.group_name_norm for g in groups if g.group_name_norm]
        if group_names:
            matches = difflib.get_close_matches(station_norm, group_names, n=1, cutoff=0.6)
            if matches:
                for group in groups:
                    if group.group_name_norm == matches[0]:
                        return group

        # 4. Fuzzy match on combined stream titles
        combined_texts = []
        for group in groups:
            combined = " ".join(
                cls._normalize_text(stream.title) or cls._normalize_text(stream.extra) or ""
                for stream in group.streams
            )
            combined_texts.append(combined)
            
        if any(combined_texts):
            matches = difflib.get_close_matches(station_norm, combined_texts, n=1, cutoff=0.55)
            if matches:
                index = combined_texts.index(matches[0])
                return groups[index]

        return None

    @classmethod
    def scrape_radio_data(cls, url: str) -> List[RadioStation]:
        """
        Complete scraping process: extract stations, streams, and match them together
        
        Args:
            url: URL of the fmstream.org page to scrape
            
        Returns:
            List of RadioStation objects with complete data and matched streams
            
        Raises:
            requests.RequestException: If HTTP requests fail
        """
        # Extract station information and stream groups
        stations_data = cls.extract_station_info(url)
        stream_groups = cls.extract_audio_streams(url)

        # Match stations to stream groups
        remaining_groups = stream_groups.copy()
        matched_groups = [None] * len(stations_data)

        for i, station_data in enumerate(stations_data):
            title = station_data.get("title", "")
            matched_group = cls.match_station_to_group(title, remaining_groups)
            
            if matched_group:
                matched_groups[i] = matched_group
                remaining_groups.remove(matched_group)

        # Assign remaining groups to unmatched stations
        remaining_iter = iter(remaining_groups)
        for i in range(len(stations_data)):
            if not matched_groups[i]:
                try:
                    matched_groups[i] = next(remaining_iter)
                except StopIteration:
                    break

        # Build final RadioStation objects
        radio_stations = []
        for i, station_data in enumerate(stations_data):
            matched_group = matched_groups[i]
            streams = []
            
            if matched_group:
                streams = [
                    AudioStream(
                        title=stream.title or stream.extra or "",
                        url=stream.url
                    )
                    for stream in matched_group.streams
                    if stream.url
                ]

            radio_station = RadioStation(
                id=i + 1,
                title=station_data.get("title", ""),
                location=station_data.get("location", ""),
                country_code=station_data.get("country_code", ""),
                genre=station_data.get("genre", ""),
                language=station_data.get("language", ""),
                frequency=station_data.get("frequency", ""),
                link=station_data.get("link", ""),
                short_desc=station_data.get("short_desc", ""),
                long_desc=station_data.get("long_desc", ""),
                streams=streams
            )
            radio_stations.append(radio_station)

        return radio_stations
