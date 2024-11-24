import logging
import httpx
import torch
from typing import List
from collections import Counter
from models.resnet9 import load_plant_disease_model
from utils.image_utils import transform_image
from config.config import IN_CHANNELS, NUM_DISEASES, CLASS_NAMES
from schemas.prediction import parse_class_name, PredictionResult, PlantHealthSummary
from fastapi import UploadFile
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nodemcu_connection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
        nodemcu_url = "http://192.168.117.147/pump/action"
        
        logger.info(f"Attempting to connect to NodeMCU at {nodemcu_url}")
        logger.info(f"Sending mix values - mix1: {mix1}, mix2: {mix2}")
        
        start_time = time.time()
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    nodemcu_url,
                    json={"mix1": mix1, "mix2": mix2},
                    timeout=mix1/1000 + 5.0
                )
                
                if response.status_code == 200:
                    logger.info(f"NodeMCU Response: {response.text}")
                else:
                    logger.warning(f"NodeMCU returned non-200 status code: {response.status_code}")
                    logger.warning(f"Response content: {response.text}")
            
            except httpx.ConnectError:
                logger.error("Failed to connect to NodeMCU - Device might be offline or IP incorrect")
            except Exception as e:
                logger.error(f"Servo control error: {str(e)}")
                logger.exception("Detailed error information:")

    async def analyze_batch(self, files: List[UploadFile]) -> PlantHealthSummary:
        logger.info(f"Starting batch analysis of {len(files)} files")
        
        if len(files) > 10:
            logger.warning("Request exceeded maximum allowed files (10)")
            raise ValueError("Maximum 10 images allowed per request.")

        predictions = []
        healthy_count = 0
        diseased_count = 0
        plant_list = []
        condition_list = []

        for file in files:
            logger.info(f"Processing file: {file.filename}")
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
                    
                logger.info(f"Successfully processed {file.filename} - Condition: {prediction.condition}")
                
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {str(e)}")
                logger.exception("Detailed error information:")
                continue

        total_plants = len(predictions)
        if total_plants == 0:
            logger.error("No valid predictions were made in the batch")
            raise ValueError("No valid predictions were made")

        healthy_percentage = (healthy_count / total_plants) * 100
        diseased_percentage = (diseased_count / total_plants) * 100

        logger.info(f"Batch analysis complete - "
                   f"Total: {total_plants}, "
                   f"Healthy: {healthy_count}, "
                   f"Diseased: {diseased_count}, "
                   f"Diseased Percentage: {diseased_percentage:.2f}%")

        most_common_plant = str(Counter(plant_list).most_common(1)[0][0])
        non_healthy_conditions = [cond for cond in condition_list if cond != "healthy"]
        most_common_condition = str(Counter(non_healthy_conditions).most_common(1)[0][0]) if non_healthy_conditions else "healthy"

        logger.info(f"Initiating pump control with diseased percentage: {diseased_percentage:.2f}%")
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