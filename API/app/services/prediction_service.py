import torch
from models.resnet9 import load_plant_disease_model
from utils.image_utils import transform_image
from config.config import IN_CHANNELS, NUM_DISEASES, CLASS_NAMES
from schemas.prediction import parse_class_name

class PredictionService:
    def __init__(self):
        self.model = load_plant_disease_model(IN_CHANNELS, NUM_DISEASES)

    async def predict(self, file):
        image = await transform_image(file)
        with torch.no_grad():
            xb = image.unsqueeze(0)
            outputs = self.model(xb)
            _, preds = torch.max(outputs, dim=1)
        
        class_name = CLASS_NAMES[preds[0].item()]
        plant, condition = parse_class_name(class_name)
        
        return {
            "predicted_plant": plant,
            "condition": condition,
            "confidence": torch.nn.functional.softmax(outputs, dim=1)[0][preds[0]].item()
        }
