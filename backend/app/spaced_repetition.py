from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SpacedRepetition:
    INITIAL_EASE = 2.5
    MIN_EASE = 1.3
    
    def __init__(self):
        self.logger = logger
    
    def calculate_next_review(self, 
                            ease_factor: float, 
                            interval: int, 
                            repetitions: int,
                            quality: int = 4) -> datetime:
        
        new_ease_factor = self._update_ease_factor(ease_factor, quality)
        
        if quality < 3:
            new_interval = 1
            new_repetitions = 0
        else:
            if repetitions == 0:
                new_interval = 1
            elif repetitions == 1:
                new_interval = 3
            else:
                new_interval = int(interval * new_ease_factor)
            
            new_repetitions = repetitions + 1
        
        next_review = datetime.now() + timedelta(days=new_interval)
        
        self.logger.info(
            f"SM-2 Update: quality={quality}, "
            f"interval={interval}->{new_interval}, "
            f"ease={ease_factor:.2f}->{new_ease_factor:.2f}, "
            f"next_review={next_review}"
        )
        
        return next_review
    
    @staticmethod
    def _update_ease_factor(ease_factor: float, quality: int) -> float:
        ef_delta = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        new_ease = max(SpacedRepetition.MIN_EASE, ease_factor + ef_delta)
        return new_ease
