from pydantic import BaseModel


class SystemTriggerRequest(BaseModel):
    user_id: str
    text: str = "summary"
    session_id: str = "default"
