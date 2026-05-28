import requests
import json
import re
from typing import List, Dict
from functools import lru_cache
from datetime import datetime, timedelta

class AIService:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self._cache = {}
        self._cache_ttl = timedelta(hours=24)  # Cache valid for 24 hours
    
    def _get_cache_key(self, prefix: str, word: str, *args) -> str:
        """Generate a unique cache key"""
        return f"{prefix}:{word.lower().strip()}:{':'.join(str(a) for a in args)}"
    
    def _get_cached(self, key: str) -> Dict | str | None:
        """Get cached value if not expired"""
        if key in self._cache:
            value, expiry = self._cache[key]
            if datetime.now() < expiry:
                return value
            del self._cache[key]
        return None
    
    def _set_cached(self, key: str, value: Dict | str) -> None:
        """Set cached value with TTL"""
        self._cache[key] = (value, datetime.now() + self._cache_ttl)
    
    def translate_trilingual(self, word: str, profession: str = "Tổng quát") -> Dict:
        """Dịch 3 ngôn ngữ song song với quy trình kiểm chứng tích hợp."""
        # Check cache first
        cache_key = self._get_cache_key("tri", word, profession)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            role = f"Chuyên gia ngành {profession}" if profession != "Tổng quát" else "Biên dịch viên"
            prompt = f"""Bạn là {role}. Hãy dịch từ '{word}' sang EN, ZH (Pinyin) và VI.
YÊU CẦU:
- Dùng thuật ngữ chuyên môn ngành {profession}.
- Kiểm tra chéo nghĩa giữa các ngôn ngữ để đảm bảo đồng nhất.
- Trả về JSON: {{"en":"...", "zh":"...", "pinyin":"...", "vi":"..."}}
Ví dụ: {{"en":"server", "zh":"服务器", "pinyin":"fúwùqì", "vi":"máy chủ"}}"""

            resp = requests.post(self.ollama_url, json={
                "model": "qwen2.5:3b",
                "prompt": prompt,
                "format": "json",
                "stream": False,
                "options": { "temperature": 0 }
            }, timeout=25)
            
            if resp.status_code == 200:
                data = json.loads(resp.json().get("response", "{}"))
                for k in data:
                    if isinstance(data[k], str):
                        data[k] = re.sub(r'[\[\]|\\/]', '', data[k]).strip()
                self._set_cached(cache_key, data)
                return data
        except Exception as e:
            print(f"!!! AI Trilingual Error: {e}")
        
        result = {"en": word, "zh": word, "pinyin": "", "vi": "Lỗi dịch thuật"}
        self._set_cached(cache_key, result)
        return result

    def translate(self, word: str, lang: str = "en", profession: str = "Tổng quát") -> str:
        """Professional Expert: Bắt buộc dịch theo thuật ngữ chuyên ngành."""
        # Check cache first
        cache_key = self._get_cache_key("trans", word, lang, profession)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            role = f"Chuyên gia cấp cao trong ngành {profession}" if profession != "Tổng quát" else "Chuyên gia ngôn ngữ"
            target = "tiếng Việt" if lang == "en" else "tiếng Việt từ tiếng Trung"
            prompt = f"""Bạn là {role}. Hãy dịch từ '{word}' sang {target}.
YÊU CẦU BẮT BUỘC: 
- Phải sử dụng đúng thuật ngữ chuyên môn của ngành {profession}.
- Trả về đúng 1-2 nghĩa sát nhất. Không giải thích."""
            
            resp = requests.post(self.ollama_url, json={
                "model": "qwen2.5:3b",
                "prompt": prompt,
                "stream": False,
                "options": { "temperature": 0 }
            }, timeout=15)
            
            if resp.status_code == 200:
                result = resp.json().get("response", "").strip()
                # Clean up: If not ZH, remove any Chinese characters that might have leaked
                if lang != "zh":
                    import re
                    result = re.sub(r'[\u4e00-\u9fff]+', '', result).strip()
                if result and len(result) < 100:
                    self._set_cached(cache_key, result)
                    return result
        except Exception as e:
            print(f"AI translate error: {e}")
        
        # Fallback dictionary
        fallback = {
            "hello": "xin chào", "goodbye": "tạm biệt", "thank": "cảm ơn",
            "restart": "khởi động lại", "printer": "máy in", "computer": "máy tính",
            "permissions": "quyền truy cập", "firewall": "tường lửa", "server": "máy chủ",
            "give": "đưa, cho", "put": "đặt, để", "get": "lấy, nhận", "hold": "cầm, giữ",
            "keep": "giữ", "drop": "đánh rơi", "catch": "bắt", "throw": "ném",
            "red": "đỏ", "blue": "xanh da trời", "green": "xanh lá cây", "yellow": "vàng",
            "black": "đen", "white": "trắng", "orange": "cam", "purple": "tím", "pink": "hồng"
        }
        result = fallback.get(word.lower(), word)
        self._set_cached(cache_key, result)
        return result
    
    def example_trilingual(self, word_en: str, word_zh: str, meaning_vi: str, profession: str = "Tổng quát") -> Dict:
        """Tạo ví dụ 3 ngôn ngữ. BẮT BUỘC chứa từ vựng trong câu."""
        # Check cache first
        cache_key = self._get_cache_key("ex_tri", f"{word_en}|{word_zh}", profession)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            prompt = f"Viết 1 câu ví dụ ngành {profession} CHỨA CẢ HAI TỪ '{word_en}' và '{word_zh}'. Trả về 1 dòng JSON: {{\"en\":\"...\", \"zh\":\"... (pinyin)\", \"vi\":\"...\"}}"
            resp = requests.post(self.ollama_url, json={
                "model": "qwen2.5:3b",
                "prompt": prompt,
                "stream": False,
                "options": { "temperature": 0, "num_predict": 300 }
            }, timeout=40)
            if resp.status_code == 200:
                text = resp.json().get("response", "").strip()
                import json, re
                match = re.search(r'\{.*\}', text)
                if match:
                    result = json.loads(match.group())
                    self._set_cached(cache_key, result)
                    return result
        except Exception as e:
            print(f"!!! AI Example Error: {e}")
        
        result = {"en": "Example error", "zh": "", "vi": ""}
        self._set_cached(cache_key, result)
        return result

    def example(self, word: str, meaning: str, lang: str = "en", profession: str = "Tổng quát") -> Dict:
        """Scenario Master: Tạo tình huống công việc chuyên sâu."""
        # Check cache first
        cache_key = self._get_cache_key("ex", word, lang, profession)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            role = f"chuyên gia làm việc trong ngành {profession}" if profession != "Tổng quát" else "người bản xứ"
            if lang == "zh":
                prompt = f"Bạn là {role}. Hãy viết 1 câu ví dụ thực tế TRONG CÔNG VIỆC dùng từ '{word}' ({meaning}). Câu phải thể hiện kiến thức chuyên sâu về {profession}. Định dạng: ZH: [câu] (Pinyin: [pinyin]) | VI: [dịch]"
                target_prefix = "ZH:"
            else:
                prompt = f"Bạn là {role}. Hãy viết 1 câu ví dụ thực tế TRONG CÔNG VIỆC dùng từ '{word}' ({meaning}). Câu phải thể hiện kiến thức chuyên sâu về {profession}. Định dạng: EN: [câu] | VI: [dịch]"
                target_prefix = "EN:"
                
            resp = requests.post(self.ollama_url, json={
                "model": "qwen2.5:3b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0
                }
            }, timeout=20)
            if resp.status_code == 200:
                text = resp.json().get("response", "")
                lines = text.strip().split('\n')
                en = ""
                vi = ""
                for line in lines:
                    if line.startswith(target_prefix):
                        en = line[len(target_prefix):].strip()
                    elif line.startswith("VI:"):
                        vi = line[3:].strip()
                if en and vi:
                    # For Chinese mode, return zh key for the example
                    if lang == "zh":
                        result = {"zh": en, "vi": vi}
                    else:
                        result = {"en": en, "vi": vi}
                    self._set_cached(cache_key, result)
                    return result
        except Exception as e:
            print(f"AI example error: {e}")
        
        # Fallback
        if lang == "zh":
            result = {"zh": f"这是使用'{word}'的例子。", "vi": f"Đây là ví dụ sử dụng '{meaning}'."}
        else:
            result = {"en": f"This is an example using '{word}'.", "vi": f"Đây là ví dụ sử dụng '{meaning}'."}
        self._set_cached(cache_key, result)
        return result
    
    def cloze(self, word: str, example: str, lang: str = "en") -> str:
        """Tạo câu điền từ vào chỗ trống (không phân biệt hoa thường)"""
        import re
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        return pattern.sub("_____", example)
    
    def conversation(self, word: str, lang: str = "en", profession: str = "Tổng quát") -> str:
        """Tạo hội thoại ngắn theo chuyên ngành"""
        # Check cache first
        cache_key = self._get_cache_key("conv", word, lang, profession)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            if lang == "zh":
                prompt = f"Bạn là một người làm trong ngành {profession}. Tạo một đoạn hội thoại công việc tiếng Trung giản thể ngắn (2 câu) sử dụng từ '{word}', có kèm theo pinyin. Nội dung xoay quanh tình huống thực tế trong ngành {profession}."
            else:
                prompt = f"Bạn là một người làm trong ngành {profession}. Tạo một đoạn hội thoại công việc tiếng Anh ngắn (2 câu) sử dụng từ '{word}'. Nội dung xoay quanh tình huống thực tế trong ngành {profession}."
                
            resp = requests.post(self.ollama_url, json={
                "model": "qwen2.5:3b",
                "prompt": prompt,
                "stream": False
            }, timeout=15)
            if resp.status_code == 200:
                result = resp.json().get("response", "")
                self._set_cached(cache_key, result)
                return result
        except Exception as e:
            print(f"AI conversation error: {e}")
        
        result = f"A: What does '{word}' mean?\nB: Let me explain with an example.\nA: I understand now!"
        self._set_cached(cache_key, result)
        return result
    
    def get_phonetics(self, word: str, lang: str = "en") -> str:
        """Tự động tạo Pinyin (cho tiếng Trung) hoặc phiên âm IPA (cho tiếng Anh)"""
        # Check cache first
        cache_key = self._get_cache_key("phon", word, lang)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            if lang == "zh":
                prompt = f"Hãy cung cấp duy nhất Pinyin có dấu thanh (tone marks) cho từ tiếng Trung '{word}'. Chỉ trả về chuỗi pinyin, không kèm bất kỳ giải thích nào khác."
            else:
                prompt = f"Hãy cung cấp phiên âm IPA quốc tế chuẩn Anh-Mỹ (IPA) cho từ tiếng Anh '{word}'. Ví dụ: /həˈloʊ/. Chỉ trả về chuỗi phiên âm nằm trong dấu gạch chéo /.../, không giải thích."
            
            resp = requests.post(self.ollama_url, json={
                "model": "qwen2.5:3b",
                "prompt": prompt,
                "stream": False,
                "options": { "temperature": 0 }
            }, timeout=10)
            if resp.status_code == 200:
                result = resp.json().get("response", "").strip()
                self._set_cached(cache_key, result)
                return result
        except Exception as e:
            print(f"AI get_phonetics error: {e}")
        
        # Fallback: simple approximation
        result = f"[{word}]" if lang == "zh" else f"/{word}/"
        self._set_cached(cache_key, result)
        return result

ai_service = AIService()
