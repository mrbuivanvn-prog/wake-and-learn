import requests
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.timeout = 30
    
    def generate_question_answer(self, topic: str) -> Dict:
        prompt = f"""Create a flashcard for {topic}.
        Response format: {{"question": "...", "answer": "..."}}"""
        
        try:
            return {
                "question": f"What is {topic}?",
                "answer": f"A comprehensive explanation of {topic}."
            }
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return {
                "question": f"What is {topic}?",
                "answer": f"Learn about {topic}."
            }
