"""
YouTube Thumbnail Extractor Module

A Python module to extract thumbnail URLs from YouTube video URLs.
Supports single URLs, lists of URLs, and multiple thumbnail quality options.
"""

import re
import urllib.parse
from typing import List, Dict, Optional
import requests
from dataclasses import dataclass


@dataclass
class ThumbnailInfo:
    """Data class to store thumbnail information"""
    video_id: str
    url: str
    maxresdefault: str
    sddefault: str
    hqdefault: str
    mqdefault: str
    default: str
    

class YouTubeThumbnailExtractor:
    """
    A class to extract YouTube video thumbnails from URLs.
    
    Supports various thumbnail qualities:
    - maxresdefault: 1280x720 (highest quality, may not exist for all videos)
    - sddefault: 640x480 (standard definition)
    - hqdefault: 480x360 (high quality)
    - mqdefault: 320x180 (medium quality)
    - default: 120x90 (lowest quality)
    """
    
    # YouTube URL patterns
    URL_PATTERNS = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})',
    ]
    
    def __init__(self):
        """Initialize the YouTube Thumbnail Extractor"""
        self.base_thumbnail_url = "https://img.youtube.com/vi/{video_id}/{quality}.jpg"
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from various YouTube URL formats.
        
        Args:
            url (str): YouTube video URL
            
        Returns:
            str: Video ID if found, None otherwise
        """
        for pattern in self.URL_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_thumbnail_urls(self, video_id: str) -> Dict[str, str]:
        """
        Generate all thumbnail URLs for a given video ID.
        
        Args:
            video_id (str): YouTube video ID
            
        Returns:
            dict: Dictionary with quality names as keys and URLs as values
        """
        qualities = ['maxresdefault', 'sddefault', 'hqdefault', 'mqdefault', 'default']
        thumbnails = {}
        
        for quality in qualities:
            thumbnails[quality] = self.base_thumbnail_url.format(
                video_id=video_id, 
                quality=quality
            )
        
        return thumbnails
    
    def check_thumbnail_exists(self, url: str) -> bool:
        """
        Check if a thumbnail URL actually exists by making a HEAD request.
        
        Args:
            url (str): Thumbnail URL to check
            
        Returns:
            bool: True if thumbnail exists, False otherwise
        """
        try:
            response = requests.head(url, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def get_best_thumbnail(self, video_id: str, 
                           quality: str = 'maxresdefault',
                           verify_existence: bool = False) -> Optional[str]:
        """
        Get the best available thumbnail URL for a video ID.
        
        Args:
            video_id (str): YouTube video ID
            verify_existence (bool): Whether to verify thumbnail exists via HTTP request
            
        Returns:
            str: Best available thumbnail URL, None if no video ID provided
        """
        if not video_id:
            return None
            
        thumbnails = self.get_thumbnail_urls(video_id)
        quality_order = [quality, 'maxresdefault', 'sddefault', 'hqdefault', 'mqdefault', 'default']
        
        if not verify_existence:
            return thumbnails['maxresdefault']
        
        # Check thumbnails in order of quality
        for quality in quality_order:
            url = thumbnails[quality]
            if self.check_thumbnail_exists(url):
                return url
        
        return thumbnails['default']  # Fallback to default
    
    def extract_thumbnail(self, 
                         url: str, 
                         quality: str = 'maxresdefault',
                         verify_existence: bool = False) -> Optional[ThumbnailInfo]:
        """
        Extract thumbnail information from a single YouTube URL.
        
        Args:
            url (str): YouTube video URL
            quality (str): Preferred thumbnail quality
            verify_existence (bool): Whether to verify thumbnail exists
            
        Returns:
            ThumbnailInfo: Thumbnail information object, None if invalid URL
        """
        video_id = self.extract_video_id(url)
        if not video_id:
            return None
        
        thumbnails = self.get_thumbnail_urls(video_id)
        
        # Determine the best URL to return
        if verify_existence:
            best_url = self.get_best_thumbnail(video_id, quality=quality, verify_existence=True)
        else:
            best_url = thumbnails.get(quality, thumbnails['maxresdefault'])
        
        return ThumbnailInfo(
            video_id=video_id,
            url=str(best_url),
            maxresdefault=thumbnails['maxresdefault'],
            sddefault=thumbnails['sddefault'],
            hqdefault=thumbnails['hqdefault'],
            mqdefault=thumbnails['mqdefault'],
            default=thumbnails['default']
        )
    
    def extract_thumbnails(self, 
                          urls: List[str], 
                          quality: str = 'maxresdefault',
                          verify_existence: bool = False) -> List[ThumbnailInfo]:
        """
        Extract thumbnails from one or multiple YouTube URLs.
        
        Args:
            urls (str or list): Single URL string or list of URL strings
            quality (str): Preferred thumbnail quality
            verify_existence (bool): Whether to verify thumbnails exist
            
        Returns:
            ThumbnailInfo or list: Single ThumbnailInfo or list of ThumbnailInfo objects
        """
        results = []
        for url in urls:
            thumbnail_info = self.extract_thumbnail(url, quality, verify_existence)
            if thumbnail_info:
                results.append(thumbnail_info)
        
        return results