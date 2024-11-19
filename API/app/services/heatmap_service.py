import torch
import numpy as np
import cv2
from PIL import Image
from torchvision import transforms
from models.cam_model import CAM
from config.websocket_config import WebSocketConfig

class HeatmapService:
    def __init__(self):
        self.config = WebSocketConfig()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self._initialize_model()
        self.transform = self._initialize_transform()

    def _initialize_model(self) -> CAM:
        model = CAM().to(self.device)
        model.load_state_dict(torch.load(self.config.MODEL_PATH))
        model.eval()
        return model

    def _initialize_transform(self):
        return transforms.Compose([
            transforms.Resize((self.config.FRAME_HEIGHT, self.config.FRAME_WIDTH)),
            transforms.ToTensor(),
        ])

    async def process_frame(self, frame_bytes: bytes, label: int = 2) -> bytes:
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)
        
        input_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            conv, _ = self.model(input_tensor)
            cam = (self.model.net.fc.weight[label][:, None, None].abs() * conv[0].abs()).sum(0)
            cam = cam.cpu().numpy()
            cam = self._normalize_cam(cam)
            
            h, w = frame.shape[:2]
            cam_resized = cv2.resize(cam, (w, h))
            heatmap = cv2.applyColorMap(cam_resized, cv2.COLORMAP_JET)
            blended_frame = cv2.addWeighted(frame, 0.6, heatmap, 0.4, 0)
            
            _, buffer = cv2.imencode('.jpg', blended_frame)
            return buffer.tobytes()

    def _normalize_cam(self, cam: np.ndarray) -> np.ndarray:
        cam -= cam.min()
        cam /= cam.max()
        return (cam * 255).astype(np.uint8)