from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
 
 
class UserMode(str, Enum):
    general = "general"
    patient = "patient"
    medical = "medical"
 
 
class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., min_length=1, max_length=5000)
    user_mode: UserMode = UserMode.general
    stream: bool = False
 
 
class ChatResponse(BaseModel):
    session_id: str
    response: str
    model_used: str
    is_emergency: bool = False
    emergency_message: str = ""
    sources: list[str] = []
    suggested_questions: list[str] = []
    has_prescription: bool = False
 
 
class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"
 
 
class ChatMessage(BaseModel):
    role: MessageRole
    content: str
 