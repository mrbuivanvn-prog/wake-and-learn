import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self):
        # Unsplash API (miễn phí, không cần key cho demo)
        self.unsplash_url = "https://unsplash.com/search/photos/"
        self.placeholder_api = "https://picsum.photos/400/300"
    
    def search_unsplash(self, query: str) -> Optional[str]:
        """Tìm ảnh từ Unsplash (dùng API công khai)"""
        try:
            # Dùng Unsplash Source API (miễn phí, không cần key)
            url = f"https://source.unsplash.com/400x300/?{query}"
            # Kiểm tra xem ảnh có tồn tại không
            response = requests.head(url, timeout=5)
            if response.status_code == 200:
                return url
        except Exception as e:
            logger.error(f"Unsplash search error: {e}")
        return None
    
    def search_pixabay(self, query: str) -> Optional[str]:
        """Tìm ảnh từ Pixabay (cần API key) - fallback"""
        # Pixabay yêu cầu API key, tạm thời bỏ qua
        return None
    
    def get_placeholder(self, query: str) -> str:
        """Ảnh placeholder với từ khóa"""
        return f"https://picsum.photos/seed/{query.replace(' ', '')}/400/300"
    
    def get_image_for_word(self, word: str) -> str:
        """Lấy ảnh cho từ (ưu tiên Unsplash -> Placeholder)"""
        # Thử Unsplash trước
        img_url = self.search_unsplash(word)
        if img_url:
            return img_url
        
        # Fallback placeholder
        return self.get_placeholder(word)
    
    def get_image_for_topic(self, topic: str) -> str:
        """Lấy ảnh theo chủ đề"""
        topic_map = {
            "animal": "cat",
            "nature": "forest",
            "technology": "computer",
            "food": "food",
            "travel": "travel",
            "business": "office",
            "science": "science",
            "art": "art"
        }
        keyword = topic_map.get(topic.lower(), topic)
        return self.get_image_for_word(keyword)
