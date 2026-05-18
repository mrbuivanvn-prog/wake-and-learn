import requests
import json
import re
from typing import List, Dict

class AIService:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
    
    def translate_trilingual(self, word: str, profession: str = "Tổng quát") -> Dict:
        """Dịch 3 ngôn ngữ song song với quy trình kiểm chứng tích hợp."""
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
                return data
        except Exception as e:
            print(f"!!! AI Trilingual Error: {e}")
        return {"en": word, "zh": word, "pinyin": "", "vi": "Lỗi dịch thuật"}

    def translate(self, word: str, lang: str = "en", profession: str = "Tổng quát") -> str:
        """Professional Expert: Bắt buộc dịch theo thuật ngữ chuyên ngành."""
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
        return fallback.get(word.lower(), word)
    
    def example_trilingual(self, word_en: str, word_zh: str, meaning_vi: str, profession: str = "Tổng quát") -> Dict:
        """Tạo ví dụ 3 ngôn ngữ. BẮT BUỘC chứa từ vựng trong câu."""
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
                    return json.loads(match.group())
        except Exception as e:
            print(f"!!! AI Example Error: {e}")
        return {"en": "Example error", "zh": "", "vi": ""}

    def example(self, word: str, meaning: str, lang: str = "en", profession: str = "Tổng quát") -> Dict:
        """Scenario Master: Tạo tình huống công việc chuyên sâu."""
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
                    return {"en": en, "vi": vi}
        except Exception as e:
            print(f"AI example error: {e}")
        
        # Fallback
        return {"en": f"This is an example using '{word}'.", "vi": f"Đây là ví dụ sử dụng '{meaning}'."}
    
    def cloze(self, word: str, example: str, lang: str = "en") -> str:
        """Tạo câu điền từ vào chỗ trống (không phân biệt hoa thường)"""
        import re
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        return pattern.sub("_____", example)
    
    def conversation(self, word: str, lang: str = "en", profession: str = "Tổng quát") -> str:
        """Tạo hội thoại ngắn theo chuyên ngành"""
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
                return resp.json().get("response", "")
        except Exception as e:
            print(f"AI conversation error: {e}")
        
        return f"A: What does '{word}' mean?\nB: Let me explain with an example.\nA: I understand now!"

ai_service = AIService()
