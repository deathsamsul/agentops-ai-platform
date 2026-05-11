from pydantic import BaseModel

# This defines the input and output format for chat 
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str