import requests
import logging
from typing import Optional
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self):
        self.cache_dir = Path("assets/images/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_image(self, query: str) -> Optional[str]:
        cached_url = self._check_cache(query)
        if cached_url:
            return cached_url
        
        image_url = self._get_placeholder_image(query)
        self._save_to_cache(query, image_url)
        return image_url
    
    def _get_placeholder_image(self, query: str) -> str:
        safe_query = query.replace(" ", "+")[:50]
        return f"https://via.placeholder.com/400x300?text={safe_query}"
    
    def _check_cache(self, query: str) -> Optional[str]:
        cache_file = self.cache_dir / f"{self._hash_query(query)}.txt"
        if cache_file.exists():
            return cache_file.read_text().strip()
        return None
    
    def _save_to_cache(self, query: str, image_url: str):
        try:
            cache_file = self.cache_dir / f"{self._hash_query(query)}.txt"
            cache_file.write_text(image_url)
        except Exception as e:
            logger.error(f"Cache save failed: {e}")
    
    @staticmethod
    def _hash_query(query: str) -> str:
        return hashlib.md5(query.lower().encode()).hexdigest()
