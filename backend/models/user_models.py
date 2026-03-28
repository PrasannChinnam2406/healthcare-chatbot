from pydantic import BaseModel, EmailStr
from typing import Optional
 
 
class UserProfile(BaseModel):
    age: Optional[int] = None
    sex: Optional[str] = None                    # male | female | other
    known_conditions: list[str] = []             # e.g. ["diabetes", "hypertension"]
    current_medications: list[str] = []          # e.g. ["Metformin 500mg"]
    allergies: list[str] = []                    # e.g. ["Penicillin"]
    user_mode: str = "general"
 
 
class UserProfileUpdate(BaseModel):
    age: Optional[int] = None
    sex: Optional[str] = None
    known_conditions: Optional[list[str]] = None
    current_medications: Optional[list[str]] = None
    allergies: Optional[list[str]] = None
    user_mode: Optional[str] = None
 
 
class SessionInfo(BaseModel):
    session_id: str
    user_mode: str
    pdf_active: bool
    pdf_filename: Optional[str]
    message_count: int
    iomt_connected: bool
    user_profile: UserProfile
 
 