from fastapi import FastAPI, Response, Query
from pydantic import BaseModel
from typing import List, Optional
from .scraper import FMStreamScraper
from .models import RadioStation, AudioStream

app = FastAPI(
    title="FMStream Clone API",
    description="API lấy danh sách kênh phát thanh và audio streams (clone kiểu fmstream.org)",
    version="1.0.0",
    contact={
        "name": "HaoWasabi",
        "url": "https://github.com/fmstream-py",
    },
)

# ================== Helpers ==================
from urllib.parse import urlencode

def build_station_list(
    c=None, hq=None, l=None, n=None, o=None, s=None, style=None
) -> List[dict]:
    base_url = "https://fmstream.org/index.php"
    params = {}
    if c: params["c"] = c
    if hq is not None: params["hq"] = hq
    if l: params["l"] = l
    if n: params["n"] = n
    if o: params["o"] = o
    if s: params["s"] = s
    if style: params["style"] = style
    url = base_url
    if params:
        url += "?" + urlencode(params)
    scraper = FMStreamScraper()
    return scraper.scrape_radio_data(url)

def _norm(s: str) -> str:
    import unicodedata
    if not s:
        return ""
    s = str(s).lower().strip()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    return s

# ================== API Endpoints ==================
@app.get("/fmstream-api", response_model=List[RadioStation], summary="API kiểu fmstream.org")
def fmstream_api(
    c: Optional[str] = Query(None, description="Country code (ITU), FT: featured, RD: random"),
    hq: Optional[int] = Query(None, description="High quality audio (0/1)"),
    l: Optional[str] = Query(None, description="Language (ISO code)"),
    n: Optional[int] = Query(0, description="Offset (skip n entries)"),
    o: Optional[str] = Query(None, description="Order/filter: top, big, med, sma, or letter"),
    s: Optional[str] = Query(None, description="Search string"),
    style: Optional[str] = Query(None, description="Station style/genre"),
):
    stations = build_station_list(c=c, hq=hq, l=l, n=n, o=o, s=s, style=style)

    # 1. Featured stations
    if c == "FT":
        # Lấy 10 kênh đầu tiên làm featured (demo)
        return stations[:10]
    # 2. Random stations
    if c == "RD":
        import random
        return random.sample(stations, min(10, len(stations)))


    # 3. Lọc theo quốc gia (location)
    if c and c not in ["FT", "RD"]:
        stations = [st for st in stations if c.lower() in (getattr(st, "location", "") or "").lower()]

    # 4. Lọc theo ngôn ngữ (chưa có trường language, demo bằng genre)
    if l:
        stations = [st for st in stations if l.lower() in (getattr(st, "genre", "") or "").lower()]

    # 5. Lọc theo chất lượng cao (hq=1: bitrate>128, demo bằng số lượng streams)
    if hq is not None:
        if hq == 1:
            stations = [st for st in stations if len(getattr(st, "streams", [])) > 1]
        else:
            stations = [st for st in stations if len(getattr(st, "streams", [])) <= 1]

    # 6. Lọc theo style/genre
    if style:
        style_norm = _norm(style)
        stations = [st for st in stations if style_norm in _norm(getattr(st, "genre", "") or "")]

    # 7. Tìm kiếm (title, genre, location, frequency)
    if s:
        s_norm = _norm(s)
        def match(st):
            return (
                s_norm in _norm(getattr(st, "title", "") or "") or
                s_norm in _norm(getattr(st, "genre", "") or "") or
                s_norm in _norm(getattr(st, "location", "") or "") or
                s_norm in _norm(getattr(st, "frequency", "") or "")
            )
        stations = [st for st in stations if match(st)]

    # 8. Lọc theo order/size
    if o:
        if o == "top":
            # Demo: sắp xếp theo số lượng streams giảm dần
            stations = sorted(stations, key=lambda st: len(getattr(st, "streams", [])), reverse=True)
        elif o == "big":
            stations = sorted(stations, key=lambda st: getattr(st, "title", ""))
        elif o == "med":
            stations = [st for st in stations if 1 < len(getattr(st, "streams", [])) < 3]
        elif o == "sma":
            stations = [st for st in stations if len(getattr(st, "streams", [])) == 1]
        else:
            # Lọc theo ký tự đầu tiên của title
            stations = [st for st in stations if (getattr(st, "title", "") or "").lower().startswith(o.lower())]

    # 9. Offset (n)
    if n:
        stations = stations[n:]

    return stations

class Stream(BaseModel):
    """Pydantic model for API stream response"""
    title: str
    url: str
    extra: str = ""

class Station(BaseModel):
    """Pydantic model for API station response"""
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
    streams: List[Stream] = []
