import logging
import httpx
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from services.prediction_service import PredictionService
from schemas.prediction import PredictionResponse, PlantHealthSummary
from typing import List
from fastapi import UploadFile
from config.config import DEBUG, HOST, PORT
from fastapi.middleware.cors import CORSMiddleware
from routers.websocket_router import router

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

app = FastAPI(debug=DEBUG)
prediction_service = PredictionService()
app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/predict", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...)):
    try:
        prediction = await prediction_service.predict(file)
        return prediction
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
@app.post("/analize-plants", response_model=PlantHealthSummary)
async def analyze_plants(files: List[UploadFile] = File(...)):
    logger.info(f"Received analyze-plants request with {len(files)} files")
    try:
        if not files or len(files) > 10:
            logger.warning(f"Invalid number of files: {len(files)}")
            return JSONResponse(
                content={"error": "Envia de 1 a 10 imagenes"},
                status_code=400
            )
        summary = await prediction_service.analyze_batch(files)
        logger.info("Analysis completed successfully")
        return summary
    except Exception as e:
        logger.error(f"Error in analyze_plants endpoint: {str(e)}")
        logger.exception("Detailed error information:")
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)