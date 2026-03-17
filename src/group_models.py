from typing import Optional

from pydantic import BaseModel, Field


class GroupCreateRequest(BaseModel):
    name: str
    members: list[dict] = Field(default_factory=list)  # [{user_id, session_id}]


class GroupUpdateRequest(BaseModel):
    name: Optional[str] = None
    members: Optional[list[dict]] = None  # [{user_id, session_id, action:"add"|"remove"}]


class GroupMessageRequest(BaseModel):
    content: str
    sender: Optional[str] = None       # 人类发消息时可省略（自动取 owner）
    sender_session: Optional[str] = ""
    mentions: Optional[list[str]] = None  # 被 @ 的 agent session key 列表 (格式: "user_id#session_id")
