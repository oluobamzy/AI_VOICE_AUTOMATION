"""
URL validator for video ingestion service.

This module provides URL validation functionality for supported video platforms.
"""

import re
import requests
from datetime import datetime, timedelta
from typing import Any, Dict, List
from urllib.parse import urlparse, parse_qs

from app.core.logging import get_logger

logger = get_logger(__name__)


class URLValidator:
    """
    URL validator for video platforms.
    
    Validates URLs for format, security, and platform support.
    """
    
    # Platform URL patterns
    URL_PATTERNS = {
        'youtube': [
            r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'https?://(?:www\.)?youtube\.com/shorts/[\w-]+',
            r'https?://youtu\.be/[\w-]+',
        ],
        'tiktok': [
            r'https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/\d+',
            r'https?://(?:vm\.)?tiktok\.com/[\w-]+',
        ],
        'instagram': [
            r'https?://(?:www\.)?instagram\.com/p/[\w-]+',
            r'https?://(?:www\.)?instagram\.com/reel/[\w-]+',
            r'https?://(?:www\.)?instagram\.com/tv/[\w-]+',
        ],
        'twitter': [
            r'https?://(?:www\.)?twitter\.com/[\w-]+/status/\d+',
            r'https?://(?:www\.)?x\.com/[\w-]+/status/\d+',
            r'https?://t\.co/[\w-]+',
        ],
    }
    
    def __init__(self):
        """Initialize URL validator."""
        self.cache_duration = timedelta(hours=1)
        self.max_cache_size = 1000
        self._validation_cache = {}
        self._cache_expiry = {}
    
    async def validate_url(self, url: str, check_accessibility: bool = True) -> Dict[str, Any]:
        """
        Validate URL for video ingestion.
        
        Args:
            url: URL to validate
            check_accessibility: Whether to check if URL is accessible
            
        Returns:
            Dict containing validation results
        """
        try:
            result = {
                'url': url,
                'is_valid': False,
                'platform': None,
                'errors': [],
                'warnings': [],
                'metadata': {}
            }
            
            # Basic format validation
            format_result = self._validate_format(url)
            if not format_result['is_valid']:
                result['errors'].extend(format_result['errors'])
                return result
            
            # Platform-specific validation
            platform_result = self._validate_platform(url)
            if platform_result['platform']:
                result['platform'] = platform_result['platform']
                result['metadata'].update(platform_result['metadata'])
                
                if not platform_result['is_valid']:
                    result['errors'].extend(platform_result['errors'])
                    return result
            else:
                result['warnings'].append('Platform not recognized or supported')
            
            # If we get here, URL is valid
            result['is_valid'] = True
            return result
            
        except Exception as e:
            logger.error(f"URL validation failed: {str(e)}")
            return {
                'url': url,
                'is_valid': False,
                'platform': None,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'metadata': {}
            }
    
    def _validate_format(self, url: str) -> Dict[str, Any]:
        """Validate basic URL format."""
        errors = []
        
        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            return {
                'is_valid': False,
                'errors': [f"Invalid URL format: {str(e)}"]
            }
        
        # Check scheme
        if not parsed.scheme:
            errors.append("URL missing scheme (http/https)")
        elif parsed.scheme not in ['http', 'https']:
            errors.append(f"Unsupported URL scheme: {parsed.scheme}")
        
        # Check netloc (domain)
        if not parsed.netloc:
            errors.append("URL missing domain")
        
        # Check URL length
        if len(url) > 2048:
            errors.append("URL too long (>2048 characters)")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_platform(self, url: str) -> Dict[str, Any]:
        """Validate URL against platform-specific patterns."""
        for platform, patterns in self.URL_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, url, re.IGNORECASE):
                    # Extract platform-specific metadata
                    metadata = self._extract_platform_metadata(url, platform)
                    
                    # Platform-specific validation
                    platform_errors = self._validate_platform_specific(url, platform, metadata)
                    
                    return {
                        'platform': platform,
                        'is_valid': len(platform_errors) == 0,
                        'errors': platform_errors,
                        'metadata': metadata
                    }
        
        return {
            'platform': None,
            'is_valid': True,
            'errors': [],
            'metadata': {}
        }
    
    def _extract_platform_metadata(self, url: str, platform: str) -> Dict[str, Any]:
        """Extract platform-specific metadata from URL."""
        metadata = {'platform': platform}
        parsed = urlparse(url)
        
        if platform == 'youtube':
            # Extract video ID
            if 'watch' in parsed.path:
                params = parse_qs(parsed.query)
                if 'v' in params:
                    metadata['video_id'] = params['v'][0]
            elif 'youtu.be' in parsed.netloc:
                metadata['video_id'] = parsed.path.lstrip('/')
            elif 'shorts' in parsed.path:
                metadata['video_id'] = parsed.path.split('/')[-1]
                metadata['is_short'] = True
        
        elif platform == 'tiktok':
            # Extract video ID
            if '/video/' in parsed.path:
                metadata['video_id'] = parsed.path.split('/video/')[-1]
            # Extract username
            if '/@' in parsed.path:
                username = parsed.path.split('/@')[1].split('/')[0]
                metadata['username'] = username
        
        elif platform == 'instagram':
            # Extract post ID
            if '/p/' in parsed.path:
                metadata['post_id'] = parsed.path.split('/p/')[-1].rstrip('/')
                metadata['content_type'] = 'post'
            elif '/reel/' in parsed.path:
                metadata['post_id'] = parsed.path.split('/reel/')[-1].rstrip('/')
                metadata['content_type'] = 'reel'
            elif '/tv/' in parsed.path:
                metadata['post_id'] = parsed.path.split('/tv/')[-1].rstrip('/')
                metadata['content_type'] = 'igtv'
        
        elif platform == 'twitter':
            # Extract tweet ID
            if '/status/' in parsed.path:
                metadata['tweet_id'] = parsed.path.split('/status/')[-1]
            # Extract username
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 1:
                metadata['username'] = path_parts[0]
        
        return metadata
    
    def _validate_platform_specific(self, url: str, platform: str, metadata: Dict[str, Any]) -> List[str]:
        """Perform platform-specific validation."""
        errors = []
        
        if platform == 'youtube':
            if not metadata.get('video_id'):
                errors.append("Could not extract YouTube video ID")
            elif len(metadata['video_id']) != 11:
                errors.append("Invalid YouTube video ID format")
        
        elif platform == 'tiktok':
            if not metadata.get('video_id'):
                errors.append("Could not extract TikTok video ID")
        
        elif platform == 'instagram':
            if not metadata.get('post_id'):
                errors.append("Could not extract Instagram post ID")
        
        elif platform == 'twitter':
            if not metadata.get('tweet_id'):
                errors.append("Could not extract Twitter tweet ID")
        
        return errors