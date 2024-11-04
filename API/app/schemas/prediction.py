from pydantic import BaseModel
from typing import List

class PredictionResult(BaseModel):
    class_name: str
    plant: str
    condition: str
    confidence: float

class PredictionResponseMulti(BaseModel):
    filename: str
    prediction: PredictionResult

class PredictionResponse(BaseModel):
    prediction: PredictionResult

class PlantHealthSummary(BaseModel):
    total_plants: int
    healthy_count: int
    diseased_count: int
    healthy_percentage: float
    diseased_percentage: float
    condition: str
    plant: str

def parse_class_name(class_name: str) -> tuple[str, str]:
    parts = class_name.split('___')
    plant = parts[0].replace('_', ' ')
    condition = parts[1].replace('_', ' ') if len(parts) > 1 else 'Unknown'
    return plant, condition