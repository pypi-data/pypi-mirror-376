"""
Custom exceptions for FMStream library
"""


class FMStreamError(Exception):
    """Base exception for FMStream library"""
    pass


class ScrapingError(FMStreamError):
    """Raised when scraping operations fail"""
    pass


class DataParsingError(FMStreamError):
    """Raised when data parsing fails"""
    pass
