from datetime import date, timedelta
from typing import Dict

class SpacedRepetitionEngine:
    
    @staticmethod
    def calculate_next_review(current_interval: int, is_correct: bool, mastery: float) -> Dict:
        if is_correct:
            new_interval = min(30, current_interval * 2)
            new_mastery = min(1.0, mastery + 0.1)
            consecutive = 1
        else:
            new_interval = 1
            new_mastery = max(0.0, mastery - 0.2)
            consecutive = 0
        
        next_review = date.today() + timedelta(days=new_interval)
        is_mastered = (new_mastery >= 0.8 and consecutive >= 5) or new_mastery >= 0.9
        
        return {
            "new_interval": new_interval,
            "new_mastery": new_mastery,
            "next_review": next_review,
            "is_mastered": is_mastered
        }
