import numpy as np

class CUSUMChangePointDetector:
    """
    Cumulative Sum (CUSUM) change-point detector to identify sudden changes in train speed or section travel times.
    Flags sudden operating changes such as unannounced signal halts, TSRs, or track issues.
    """
    def __init__(self, threshold: float = 15.0, drift: float = 5.0):
        self.threshold = threshold
        self.drift = drift
        self.reset()

    def reset(self):
        self.s_pos = 0.0
        self.s_neg = 0.0
        self.mean = None
        self.window = []

    def add_data_point(self, value: float) -> dict:
        self.window.append(value)
        if len(self.window) > 20:
            self.window.pop(0)
            
        if self.mean is None:
            self.mean = value
            return {"change_detected": False, "direction": None, "score": 0.0}
            
        # Update running mean
        self.mean = np.mean(self.window)
        
        # CUSUM calculations
        self.s_pos = max(0.0, self.s_pos + (value - self.mean - self.drift))
        self.s_neg = max(0.0, self.s_neg + (self.mean - value - self.drift))
        
        if self.s_pos > self.threshold:
            score = self.s_pos
            self.s_pos = 0.0
            return {"change_detected": True, "direction": "SPEED_INCREASE", "score": float(score)}
            
        if self.s_neg > self.threshold:
            score = self.s_neg
            self.s_neg = 0.0
            return {"change_detected": True, "direction": "SPEED_DROP", "score": float(score)}
            
        return {"change_detected": False, "direction": None, "score": max(self.s_pos, self.s_neg)}
