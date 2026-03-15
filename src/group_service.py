import asyncio
import os
import secrets
import time
from typing import Any, Callable

import httpx
from fastapi import HTTPException

from auth_utils import extract_user_password_session, is_internal_bearer, parse_bearer_parts
from checkpoint_repository import list_thread_ids_by_prefix
from group_repository import (
    add_group_member,
    create_group_with_members,
    delete_group as delete_group_records,
    get_group,
    get_group_owner,
    group_exists,
    init_group_db as init_group_db_repo,
    insert_group_message,
    list_group_member_targets,
    list_group_members,
    list_group_messages_after,
    list_groups_for_user,
    list_recent_group_messages,
    remove_group_member,
    update_group_name,
)
from group_models import GroupCreateRequest, GroupMessageRequest, GroupUpdateRequest
from logging_utils import get_logger
from session_summary import first_human_title

logger = get_logger("group_service")


async def init_group_db(group_db_path: str) -> None:
    """初始化群聊数据库表结构。"""
    await init_group_db_repo(group_db_path)


class GroupService:
    def __init__(
        self,
        *,
        internal_token: str,
        verify_password: Callable[[str, str], bool],
        checkpoint_db_path: str,
        group_db_path: str,
        agent: Any,
    ):
        self.internal_token = internal_token
        self.verify_password = verify_password
        self.checkpoint_db_path = checkpoint_db_path
        self.group_db_path = group_db_path
        self.agent = agent
        self.group_muted: set[str] = set()

    def parse_group_auth(self, authorization: str | None):
        """从 Bearer token 解析用户认证，返回 (user_id, password, session_id)。"""
        parts = parse_bearer_parts(authorization)
        if not parts:
            raise HTTPException(status_code=401, detail="Missing Authorization header")
        if len(parts) < 2:
            raise HTTPException(status_code=401, detail="Invalid token format")

        if is_internal_bearer(parts, self.internal_token):
            uid = parts[1] if len(parts) >= 2 and parts[1] else "system"
            sid = parts[2] if len(parts) > 2 else "default"
            return uid, "", sid

        parsed = extract_user_password_session(parts, default_session="default")
        if not parsed:
            raise HTTPException(status_code=401, detail="Invalid token format")
        uid, pw, sid = parsed
        if not self.verify_password(uid, pw):
            raise HTTPException(status_code=401, detail="认证失败")
        return uid, pw, sid

    async def get_agent_title(self, user_id: str, session_id: str) -> str:
        """从 checkpoint 提取 agent 的 session title（第一条非系统触发 HumanMessage 前50字）。"""
        tid = f"{user_id}#{session_id}"
        try:
            config = {"configurable": {"thread_id": tid}}
            snapshot = await self.agent.agent_app.aget_state(config)
            msgs = snapshot.values.get("messages", []) if snapshot and snapshot.values else []
            title = first_human_title(
                msgs,
                skip_prefixes=("[系统触发]", "[外部学术会议邀请]", "[群聊"),
                title_len=50,
                list_fallback="",
                default=session_id,
            )
            return title
        except Exception:
            pass
        return session_id

    async def broadcast_to_group(
        self,
        group_id: str,
        sender: str,
        content: str,
        exclude_user: str = "",
        exclude_session: str = "",
        mentions: list[str] | None = None,
    ):
        """向群内 agent 成员广播消息（异步 fire-and-forget）。"""
        if group_id in self.group_muted:
            logger.info("群 %s 已静音，跳过广播", group_id)
            return
        members = await list_group_member_targets(self.group_db_path, group_id)

        for user_id, session_id, is_agent in members:
            if group_id in self.group_muted:
                logger.info("群 %s 广播中途被静音，停止", group_id)
                return
            if not is_agent:
                continue
            if user_id == exclude_user and session_id == exclude_session:
                continue

            member_key = f"{user_id}#{session_id}"
            if mentions and member_key not in mentions:
                continue

            my_title = await self.get_agent_title(user_id, session_id)
            trigger_url = f"http://127.0.0.1:{os.getenv('PORT_AGENT', '51200')}/system_trigger"

            if mentions and member_key in mentions:
                msg_text = (f"[群聊 {group_id}] {sender} @你 说:\n{content}\n\n"
                            f"(⚠️ 这是专门 @你 的消息，你必须回复！"
                            f"你在群聊中的身份/角色是「{my_title}」，回复时请体现你的专业角色视角。"
                            f"请使用 send_to_group 工具回复，group_id={group_id}。)")
            else:
                msg_text = (f"[群聊 {group_id}] {sender} 说:\n{content}\n\n"
                            f"(你在群聊中的身份/角色是「{my_title}」，回复时请体现你的专业角色视角。"
                            f"仅当消息与你直接相关、点名你、向你提问、或面向所有人时，"
                            f"才使用 send_to_group 工具回复，group_id={group_id}。"
                            f"其他情况请忽略，不要回应。)")
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    await client.post(
                        trigger_url,
                        headers={"X-Internal-Token": self.internal_token},
                        json={
                            "user_id": user_id,
                            "session_id": session_id,
                            "text": msg_text,
                        },
                    )
            except Exception as e:
                logger.warning("广播到 %s#%s 失败: %s", user_id, session_id, e)

    async def create_group(self, req: GroupCreateRequest, authorization: str | None):
        uid, _, _ = self.parse_group_auth(authorization)
        group_id = f"g_{int(time.time()*1000)}_{secrets.token_hex(4)}"
        now = time.time()
        await create_group_with_members(
            self.group_db_path,
            group_id=group_id,
            name=req.name,
            owner=uid,
            created_at=now,
            members=req.members,
        )
        return {"group_id": group_id, "name": req.name, "owner": uid}

    async def list_groups(self, authorization: str | None):
        uid, _, _ = self.parse_group_auth(authorization)
        return await list_groups_for_user(self.group_db_path, uid)

    async def get_group(self, group_id: str, authorization: str | None):
        self.parse_group_auth(authorization)
        group = await get_group(self.group_db_path, group_id)
        if not group:
            raise HTTPException(status_code=404, detail="群聊不存在")

        members = await list_group_members(self.group_db_path, group_id)
        for member in members:
            if not member.get("is_agent"):
                continue
            member["title"] = await self.get_agent_title(member["user_id"], member["session_id"])

        messages = await list_recent_group_messages(self.group_db_path, group_id, limit=100)
        return {**group, "members": members, "messages": messages}

    async def get_group_messages(self, group_id: str, after_id: int, authorization: str | None):
        self.parse_group_auth(authorization)
        messages = await list_group_messages_after(self.group_db_path, group_id, after_id, limit=200)
        return {"messages": messages}

    async def post_group_message(
        self,
        group_id: str,
        req: GroupMessageRequest,
        authorization: str | None,
        x_internal_token: str | None,
    ):
        sender = ""
        sender_session = req.sender_session or ""

        if x_internal_token and x_internal_token == self.internal_token:
            sender = req.sender or "agent"
        else:
            uid, _, sid = self.parse_group_auth(authorization)
            sender = uid
            sender_session = sid

        now = time.time()
        if not await group_exists(self.group_db_path, group_id):
            raise HTTPException(status_code=404, detail="群聊不存在")
        msg_id = await insert_group_message(
            self.group_db_path,
            group_id=group_id,
            sender=sender,
            sender_session=sender_session,
            content=req.content,
            timestamp=now,
        )

        exclude_uid = sender.split("#")[0] if "#" in sender else sender
        asyncio.create_task(
            self.broadcast_to_group(
                group_id,
                sender,
                req.content,
                exclude_user=exclude_uid,
                exclude_session=sender_session,
                mentions=req.mentions,
            )
        )

        return {"status": "sent", "sender": sender, "timestamp": now, "id": msg_id}

    async def update_group(self, group_id: str, req: GroupUpdateRequest, authorization: str | None):
        uid, _, _ = self.parse_group_auth(authorization)
        owner = await get_group_owner(self.group_db_path, group_id)
        if not owner:
            raise HTTPException(status_code=404, detail="群聊不存在")
        if owner != uid:
            raise HTTPException(status_code=403, detail="只有群主可以修改群设置")

        if req.name:
            await update_group_name(self.group_db_path, group_id, req.name)

        if req.members:
            now = time.time()
            for m in req.members:
                action = m.get("action", "add")
                m_uid = m.get("user_id", "")
                m_sid = m.get("session_id", "default")
                if not m_uid:
                    continue
                if action == "add":
                    await add_group_member(
                        self.group_db_path,
                        group_id=group_id,
                        user_id=m_uid,
                        session_id=m_sid,
                        joined_at=now,
                    )
                elif action == "remove":
                    await remove_group_member(
                        self.group_db_path,
                        group_id=group_id,
                        user_id=m_uid,
                        session_id=m_sid,
                    )
        return {"status": "updated"}

    async def delete_group(self, group_id: str, authorization: str | None):
        uid, _, _ = self.parse_group_auth(authorization)
        owner = await get_group_owner(self.group_db_path, group_id)
        if not owner:
            raise HTTPException(status_code=404, detail="群聊不存在")
        if owner != uid:
            raise HTTPException(status_code=403, detail="只有群主可以删除群")
        await delete_group_records(self.group_db_path, group_id)
        return {"status": "deleted"}

    async def mute_group(self, group_id: str, authorization: str | None):
        self.parse_group_auth(authorization)
        self.group_muted.add(group_id)
        return {"status": "muted", "group_id": group_id}

    async def unmute_group(self, group_id: str, authorization: str | None):
        self.parse_group_auth(authorization)
        self.group_muted.discard(group_id)
        return {"status": "unmuted", "group_id": group_id}

    async def group_mute_status(self, group_id: str, authorization: str | None):
        self.parse_group_auth(authorization)
        return {"muted": group_id in self.group_muted}

    async def list_available_sessions(self, group_id: str, authorization: str | None):
        uid, _, _ = self.parse_group_auth(authorization)
        prefix = f"{uid}#"
        sessions = []
        try:
            rows = await list_thread_ids_by_prefix(self.checkpoint_db_path, prefix)

            for thread_id in rows:
                sid = thread_id[len(prefix):]
                config = {"configurable": {"thread_id": thread_id}}
                snapshot = await self.agent.agent_app.aget_state(config)
                msgs = snapshot.values.get("messages", []) if snapshot and snapshot.values else []
                first_human = first_human_title(
                    msgs,
                    skip_prefixes=("[系统触发]", "[外部学术会议邀请]"),
                    title_len=80,
                    list_fallback="(图片消息)",
                    default="",
                )

                sessions.append({
                    "session_id": sid,
                    "title": first_human or f"Session {sid}",
                })
        except Exception as e:
            return {"sessions": [], "error": str(e)}

        return {"sessions": sessions}
