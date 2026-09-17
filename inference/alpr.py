import re
from fast_alpr import ALPR
from config import CONFIG

class ALPRENGINE:
    def __init__(self):
        self.alpr = ALPR(detector_model=CONFIG.model.detector_model, 
                        ocr_model=CONFIG.model.ocr_model,
                        detector_conf_thresh=CONFIG.model.detector_confidence,
                        ocr_device=CONFIG.model.ocr_device)
  
    def detect(self,frame: any):
        return self.alpr.predict(frame)
    
    def normalise_plate(self, text: str, min_len: int = 2, max_len: int = 10):
        reg = re.compile(r"[^A-Z0-9]")
        cleaned = reg.sub("", text.upper())
        if min_len <= len(cleaned) <= max_len:
            return cleaned
        return None
    