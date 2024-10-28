from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from services.prediction_service import PredictionService
from schemas.prediction import PredictionResponse, PlantHealthSummary
from typing import List
from fastapi import UploadFile
from config.config import DEBUG, HOST, PORT

app = FastAPI(debug=DEBUG)
prediction_service = PredictionService()

@app.post("/predict", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...)):
    try:
        prediction = await prediction_service.predict(file)
        return prediction
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
@app.post("/analize-plats", response_model=PlantHealthSummary)
async def analyze_plants(files: List[UploadFile] = File(...)):
    try:
        if not files or len(files) > 10:
            return JSONResponse(
                content={"error": "Envia de 1 a 10 imagenes"},
                status_code=400
            )
        summary = await prediction_service.analyze_batch(files)
        return summary
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)