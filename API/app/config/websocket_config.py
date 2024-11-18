from pydantic import BaseModel
import os
from dotenv import load_dotenv

class WebSocketConfig(BaseModel):
    FRAME_RATE: int = 30
    MAX_CONNECTIONS: int = 10
    FRAME_WIDTH: int = 512
    FRAME_HEIGHT: int = 344
    MODEL_PATH: str = os.getenv('CAM_MODEL_PATH', 'model_for_cam.pth')