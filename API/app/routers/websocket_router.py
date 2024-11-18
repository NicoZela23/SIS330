# routers/websocket_router.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.heatmap_service import HeatmapService
from utils.frame_processing import FrameProcessor
import json

router = APIRouter()
heatmap_service = HeatmapService()
frame_processor = FrameProcessor()

@router.websocket("/ws/heatmap")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Receive frame data
            frame_data = await websocket.receive_text()
            
            try:
                # Decode the frame
                frame_bytes = frame_processor.decode_frame(frame_data)
                
                # Process the frame
                processed_frame = await heatmap_service.process_frame(frame_bytes)
                
                # Encode and send back the processed frame
                response_data = frame_processor.encode_frame(processed_frame)
                await websocket.send_text(response_data)
                
            except ValueError as e:
                await websocket.send_json({"error": str(e)})
                
    except WebSocketDisconnect:
        print("Client disconnected")