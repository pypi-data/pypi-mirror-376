"""
YouTube Thumbnail Extractor

A Python module to extract thumbnail URLs from YouTube video URLs
with support for multiple quality options and URL verification.
"""

from .extract_thumbnails import YouTubeThumbnailExtractor, ThumbnailInfo

__version__ = "1.0.0"
__author__ = "Kevin"
__email__ = "kevin@cattt.space"
__description__ = "A Python module to extract thumbnail URLs from YouTube video URLs with multiple quality options"

__all__ = ['YouTubeThumbnailExtractor', 'ThumbnailInfo']