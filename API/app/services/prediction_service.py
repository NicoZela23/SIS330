import torch
from app.models import load_plant_disease_model
from app.utils.image_utils import transform_image
from config.config import IN_CHANNELS, NUM_DISEASES, CLASS_NAMES
from app.schemas.prediction import PredictionResult, PredictionResponse, parse_class_name

class PredictionService:
    def __init__(self):
        self.model = load_plant_disease_model(IN_CHANNELS, NUM_DISEASES)

    async def predict(self, file):
        image = await transform_image(file)
        with torch.no_grad():
            outputs = self.model(image.unsqueeze(0))
            probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
            top_3_probs, top_3_indices = torch.topk(probabilities, 3)

        top_3_predictions = []
        for prob, idx in zip(top_3_probs, top_3_indices):
            class_name = CLASS_NAMES[idx]
            plant, condition = parse_class_name(class_name)
            prediction = PredictionResult(
                class_name=class_name,
                plant=plant,
                condition=condition,
                confidence=prob.item()
            )
            top_3_predictions.append(prediction)

        return PredictionResponse(
            prediction=top_3_predictions[0],
            top_3_predictions=top_3_predictions
        )