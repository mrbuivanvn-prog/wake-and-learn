import ollama
import json
import logging
from deep_translator import GoogleTranslator
from typing import Dict

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self, model_name: str = "qwen2.5:3b"):
        self.model_name = model_name
        self.translator = GoogleTranslator(source='en', target='vi')
        logger.info(f"✅ AI Service with Google Translate + Ollama")
    
    def generate_bilingual_card(self, word: str) -> Dict:
        """Tạo thẻ song ngữ"""
        # Dịch từ chính
        vietnamese = self.translator.translate(word)
        
        # Lấy ví dụ từ Ollama
        prompt = f"""Tạo 2 câu ví dụ tiếng Anh với từ "{word}".
Trả về JSON: {{"examples": ["câu 1", "câu 2"]}}"""
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.7}
            )
            text = response['message']['content'].strip()
            text = text.replace('```json', '').replace('```', '')
            data = json.loads(text)
            examples_en = data.get("examples", [f"Example with {word}"])
        except:
            examples_en = [f"This is an example with {word}", f"Another example with {word}"]
        
        # Dịch ví dụ
        examples_vn = [self.translator.translate(ex) for ex in examples_en]
        
        return {
            "question": word,
            "answer": vietnamese,
            "question_vn": f"{word} nghĩa là gì?",
            "answer_en": word,
            "topic": "Vocabulary",
            "difficulty": "medium",
            "examples_en": "\n".join(examples_en),
            "examples_vn": "\n".join(examples_vn)
        }
    
    def chat_help(self, question: str) -> str:
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": f"Trả lời bằng tiếng Việt: {question}"}]
            )
            return response['message']['content']
        except:
            return "Xin lỗi, tôi đang gặp lỗi."
