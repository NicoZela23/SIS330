from pydantic import BaseModel
from typing import List

class PredictionResult(BaseModel):
    class_name: str
    plant: str
    condition: str
    confidence: float

class PredictionResponse(BaseModel):
    prediction: PredictionResult

def parse_class_name(class_name: str) -> tuple[str, str]:
    parts = class_name.split('___')
    plant = parts[0].replace('_', ' ')
    condition = parts[1].replace('_', ' ') if len(parts) > 1 else 'Unknown'
    return plant, condition