# FMStream Library

A Python library for scraping FM radio station data from fmstream.org with REST API support.

## Features

- Extract FM radio station information (title, location, frequency, etc.)
- Parse audio stream URLs from JavaScript data
- Intelligent matching of stations with their corresponding streams
- Clean, structured data models using dataclasses
- Type hints for better code documentation
- FastAPI REST API with filtering and search capabilities
- Compatible with fmstream.org API parameters

## Installation

```bash
pip install fmstream
```

For API server support:
```bash
pip install fmstream[api]
```

## Quick Start

### Python Library Usage

```python
from fmstream import FMStreamScraper

# Scrape radio station data from a fmstream.org URL
url = "https://fmstream.org/country/vietnam"
scraper = FMStreamScraper()
stations = scraper.scrape_stations(url)

# Access station information
for station in stations:
    print(f"Station: {station.title}")
    print(f"Location: {station.location}")
    print(f"Frequency: {station.frequency}")
    print(f"Streams: {len(station.streams)}")
    
    # Access audio streams
    for stream in station.streams:
        print(f"  - {stream.title}: {stream.url}")
```

### REST API Usage

Start the API server:

```python
import uvicorn
from fmstream import fastapi_app

uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)
```

Or use the example script:

```bash
python examples/api_server.py
```

Access the API:

```bash
# Get all stations
curl "http://localhost:8000/fmstream-api"

# Search for stations
curl "http://localhost:8000/fmstream-api?s=radio&c=VN"

# Get featured stations
curl "http://localhost:8000/fmstream-api?c=FT"

# Filter by genre/style
curl "http://localhost:8000/fmstream-api?style=pop"
```

API Documentation: http://localhost:8000/docs

### API Parameters

- `c`: Country code (ITU), "FT" for featured, "RD" for random
- `hq`: High quality audio (0/1)
- `l`: Language (ISO code)
- `n`: Offset (skip n entries)
- `o`: Order/filter (top, big, med, sma, or letter)
- `s`: Search string
- `style`: Station style/genre

## API Reference

### FMStreamScraper

Main scraper class with methods:

- `scrape_stations(url)` - Complete scraping process
- `extract_station_info(url)` - Extract station metadata only
- `extract_audio_streams(url)` - Extract stream data only
- `match_station_to_group(title, groups)` - Match station to stream group

### Data Models

- `RadioStation` - Complete radio station with metadata and streams
- `AudioStream` - Individual audio stream with title and URL
- `StreamGroup` - Group of related audio streams


## Legal & Data Source Notice

- This library uses data scraped from [fmstream.org](https://fmstream.org/).
- **For non-commercial use only.** No ads, no fees, no user tracking.
- Do **not** store or aggregate stream URLs or metadata in your own database.
- You must clearly credit fmstream.org as the data source and provide a visible link in your application.
- You are solely responsible for any legal issues arising from use of this data.
- See [fmstream.org API Terms](https://fmstream.org/api.htm) for full conditions.

## Requirements

- Python 3.7+
- requests
- beautifulsoup4
- fastapi (for API server)
- pydantic (for API server)
- uvicorn (for API server)

## License

[MIT License][def]


[def]: LICENSE