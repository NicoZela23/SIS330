from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.heatmap_service import HeatmapService
from utils.frame_processing import FrameProcessor

router = APIRouter()
heatmap_service = HeatmapService()
frame_processor = FrameProcessor()

@router.websocket("/ws/heatmap")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            frame_data = await websocket.receive_text()
            try:
                frame_bytes = frame_processor.decode_frame(frame_data)
                processed_frame = await heatmap_service.process_frame(frame_bytes)
                response_data = frame_processor.encode_frame(processed_frame)
                await websocket.send_text(response_data)
                
            except ValueError as e:
                await websocket.send_json({"error": str(e)})
                
    except WebSocketDisconnect:
        print("Client disconnected")