import requests
import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AudioService:
    def __init__(self):
        # Dùng Google Text-to-Speech API miễn phí
        self.tts_api_url = "https://translate.google.com/translate_tts"
    
    def get_audio_url(self, text: str, lang: str = "en") -> str:
        """Tạo URL để phát âm thanh"""
        # Dùng Google TTS (miễn phí, không cần API key)
        return f"https://translate.google.com/translate_tts?ie=UTF-8&q={text}&tl={lang}&client=tw-ob"
    
    def get_audio_base64(self, text: str, lang: str = "en") -> Optional[str]:
        """Lấy audio dạng base64 để nhúng trực tiếp"""
        try:
            response = requests.get(
                f"https://translate.google.com/translate_tts",
                params={
                    "ie": "UTF-8",
                    "q": text,
                    "tl": lang,
                    "client": "tw-ob",
                    "ttsspeed": 1.0
                },
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                timeout=10
            )
            if response.status_code == 200:
                return base64.b64encode(response.content).decode('utf-8')
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
        return None
