from dataclasses import dataclass

@dataclass()
class PlateInfo:
    plate: str
    confidence: float
    frame: object
    timestamp: float = None
    starttimestamp: float = None
    endtimestamp: float = None
    image: object = None  