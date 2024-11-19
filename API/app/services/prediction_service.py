import httpx
import torch
from typing import List
from collections import Counter
from models.resnet9 import load_plant_disease_model
from utils.image_utils import transform_image
from config.config import IN_CHANNELS, NUM_DISEASES, CLASS_NAMES
from schemas.prediction import parse_class_name, PredictionResult, PlantHealthSummary
from fastapi import UploadFile

class PredictionService:
    def __init__(self):
        self.model = load_plant_disease_model(IN_CHANNELS, NUM_DISEASES)

    async def predict(self, file) -> PredictionResult:
        image = await transform_image(file)
        with torch.no_grad():
            xb = image.unsqueeze(0)
            outputs = self.model(xb)
            _, preds = torch.max(outputs, dim=1)
        
        class_name = CLASS_NAMES[preds[0].item()]
        plant, condition = parse_class_name(class_name)
        confidence = torch.nn.functional.softmax(outputs, dim=1)[0][preds[0]].item()

        return PredictionResult(
            class_name=class_name,
            plant=plant,
            condition=condition,
            confidence=confidence
        )
    
    async def control_pump(self, diseased_percentage: float) -> None:
        mix1 = int((diseased_percentage * 100) / 1.7)
        mix2 = mix1/2

        nodemcu_url = "http://192.168.71.147/pump/action"
        
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    nodemcu_url,
                    json={"mix1": mix1, "mix2": mix2},
                    timeout=mix1/1000 + 5.0
                )
            except Exception as e:
                print(f"Servo control error: {str(e)}")
    
    async def analyze_batch(self, files: List[UploadFile]) -> PlantHealthSummary:
        if len(files) > 10:
            raise ValueError("Maximum 10 images allowed per request.")

        predictions = []
        healthy_count = 0
        diseased_count = 0
        plant_list = []
        condition_list = []

        for file in files:
            try:
                prediction = await self.predict(file)
                predictions.append({
                    "filename": file.filename,
                    "prediction": prediction
                })

                plant_list.append(prediction.plant)
                condition_list.append(prediction.condition)
                
                if prediction.condition.lower() == "healthy":
                    healthy_count += 1
                else:
                    diseased_count += 1
            except Exception as e:
                print(f"Error processing file {file.filename}: {str(e)}")
                continue

        total_plants = len(predictions)
        if total_plants == 0:
            raise ValueError("No valid predictions were made")

        healthy_percentage = (healthy_count / total_plants) * 100
        diseased_percentage = (diseased_count / total_plants) * 100

        most_common_plant = str(Counter(plant_list).most_common(1)[0][0])
        non_healthy_conditions = [cond for cond in condition_list if cond != "healthy"]
        most_common_condition = str(Counter(non_healthy_conditions).most_common(1)[0][0]) if non_healthy_conditions else "healthy"

        await self.control_pump(diseased_percentage)

        return PlantHealthSummary(
            total_plants=total_plants,
            healthy_count=healthy_count,
            diseased_count=diseased_count,
            healthy_percentage=healthy_percentage,
            diseased_percentage=diseased_percentage,
            condition=most_common_condition,
            plant=most_common_plant 
        )