from typing import Optional

from pydantic import BaseModel


class LoginRequest(BaseModel):
    user_id: str
    password: str


class CancelRequest(BaseModel):
    user_id: str
    password: str = ""  # Optional when using X-Internal-Token
    session_id: str = "default"


class TTSRequest(BaseModel):
    user_id: str
    password: str = ""  # Optional when using X-Internal-Token
    text: str
    voice: Optional[str] = None
