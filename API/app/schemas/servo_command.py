from pydantic import BaseModel

class ServoCommand(BaseModel):
    angle: int