from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from app.services.prediction_service import PredictionService
from app.schemas.prediction import PredictionResponse

app = FastAPI()
prediction_service = PredictionService()

@app.post("/predict", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...)):
    try:
        prediction = await prediction_service.predict(file)
        return prediction
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)