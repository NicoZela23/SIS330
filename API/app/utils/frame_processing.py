import base64
from typing import Tuple

class FrameProcessor:
    @staticmethod
    def decode_frame(frame_data: str) -> bytes:
        """Decode base64 frame data to bytes"""
        try:
            return base64.b64decode(frame_data)
        except Exception as e:
            raise ValueError(f"Error decoding frame: {str(e)}")

    @staticmethod
    def encode_frame(frame_bytes: bytes) -> str:
        """Encode frame bytes to base64 string"""
        return base64.b64encode(frame_bytes).decode('utf-8')