import requests
from typing import List, Dict

class AIService:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
    
    def translate(self, word: str, lang: str = "en") -> str:
        """Dịch từ sang tiếng Việt"""
        try:
            if lang == "zh":
                prompt = f"Dịch từ tiếng Trung '{word}' sang tiếng Việt. Nếu từ có nhiều nghĩa, hãy liệt kê 2-3 nghĩa THÔNG DỤNG nhất, cách nhau bằng dấu phẩy. Định dạng: [Nghĩa] (Pinyin: [Phiên âm]). Chỉ trả về nghĩa, không giải thích."
            else:
                prompt = f"Dịch từ tiếng Anh '{word}' sang tiếng Việt. Nếu từ có nhiều nghĩa, hãy liệt kê 2-3 nghĩa THÔNG DỤNG nhất, cách nhau bằng dấu phẩy. Tuyệt đối không dùng từ lạ, từ cổ hay từ không tự nhiên. Chỉ trả về các nghĩa, không giải thích."
                
            resp = requests.post(self.ollama_url, json={
                "model": "qwen2.5:3b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0
                }
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
    
    def example(self, word: str, meaning: str, lang: str = "en") -> Dict:
        """Tạo ví dụ kèm bản dịch"""
        try:
            if lang == "zh":
                prompt = f"""Bạn là giáo viên mầm non. Hãy lấy nghĩa đầu tiên của '{meaning}' và tạo 1 câu ví dụ CỰC KỲ ĐƠN GIẢN cho trẻ em bằng tiếng Trung (giản thể) sử dụng từ '{word}' theo đúng nghĩa đó.
Trả về đúng định dạng:
ZH: [câu tiếng Trung đơn giản] (Pinyin: [phiên âm pinyin])
VI: [câu tiếng Việt]"""
                target_prefix = "ZH:"
            else:
                prompt = f"""Bạn là giáo viên mầm non. Hãy lấy nghĩa đầu tiên của '{meaning}' và tạo 1 câu ví dụ CỰC KỲ ĐƠN GIẢN cho trẻ em bằng tiếng Anh sử dụng từ '{word}' theo đúng nghĩa đó.
Trả về đúng định dạng:
EN: [câu tiếng Anh đơn giản]
VI: [câu tiếng Việt]"""
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
    
    def conversation(self, word: str, lang: str = "en") -> str:
        """Tạo hội thoại ngắn"""
        try:
            if lang == "zh":
                prompt = f"Bạn là giáo viên mầm non. Tạo một đoạn hội thoại tiếng Trung giản thể cực ngắn (2 câu) cho trẻ em sử dụng từ '{word}', có kèm theo pinyin. Nội dung vui vẻ về đồ chơi hoặc trường học."
            else:
                prompt = f"Bạn là giáo viên mầm non. Tạo một đoạn hội thoại tiếng Anh cực ngắn (2 câu) cho trẻ em sử dụng từ '{word}'. Nội dung vui vẻ, đơn giản về đồ chơi hoặc trường học."
                
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
