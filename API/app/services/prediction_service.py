import torch
from typing import List
from models.resnet9 import load_plant_disease_model
from utils.image_utils import transform_image
from config.config import IN_CHANNELS, NUM_DISEASES, CLASS_NAMES
from schemas.prediction import parse_class_name, PredictionResult, PlantHealthSummary
from fastapi import UploadFile

class PredictionService:
    def __init__(self):
        self.model = load_plant_disease_model(IN_CHANNELS, NUM_DISEASES)

    async def predict(self, file) -> PredictionResult:  # Note: Changed return type
        image = await transform_image(file)
        with torch.no_grad():
            xb = image.unsqueeze(0)
            outputs = self.model(xb)
            _, preds = torch.max(outputs, dim=1)
        
        class_name = CLASS_NAMES[preds[0].item()]
        plant, condition = parse_class_name(class_name)
        confidence = torch.nn.functional.softmax(outputs, dim=1)[0][preds[0]].item()

        # Return PredictionResult directly, not wrapped in a dict
        return PredictionResult(
            class_name=class_name,
            plant=plant,
            condition=condition,
            confidence=confidence
        )
    
    async def analyze_batch(self, files: List[UploadFile]) -> PlantHealthSummary:
        if len(files) > 10:
            raise ValueError("Maximum 10 images allowed per request.")

        predictions = []
        healthy_count = 0
        diseased_count = 0

        for file in files:
            try:
                prediction = await self.predict(file)  # Now returns PredictionResult directly
                predictions.append({
                    "filename": file.filename,
                    "prediction": prediction
                })
                
                # Now we can access condition directly
                if prediction.condition.lower() == "healthy":
                    healthy_count += 1
                else:
                    diseased_count += 1
            except Exception as e:
                # Optional: Handle individual file prediction errors
                print(f"Error processing file {file.filename}: {str(e)}")
                continue

        total_plants = len(predictions)  # Use actual successful predictions
        if total_plants == 0:
            raise ValueError("No valid predictions were made")

        healthy_percentage = (healthy_count / total_plants) * 100
        diseased_percentage = (diseased_count / total_plants) * 100

        return PlantHealthSummary(
            total_plants=total_plants,
            healthy_count=healthy_count,
            diseased_count=diseased_count,
            healthy_percentage=healthy_percentage,
            diseased_percentage=diseased_percentage,
            predictions=predictions
        )