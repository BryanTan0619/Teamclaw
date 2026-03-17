import os
from typing import Any, Callable

import httpx
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from auth_utils import extract_user_password_session, is_internal_bearer, parse_bearer_parts
from logging_utils import get_logger
from ops_models import CancelRequest, LoginRequest, TTSRequest

logger = get_logger("ops_service")


class OpsService:
    def __init__(
        self,
        *,
        internal_token: str,
        agent: Any,
        verify_password: Callable[[str, str], bool],
        verify_auth_or_token: Callable[[str, str, str | None], None],
    ):
        self.internal_token = internal_token
        self.agent = agent
        self.verify_password = verify_password
        self.verify_auth_or_token = verify_auth_or_token

    async def get_tools_list(self, x_internal_token: str | None, authorization: str | None):
        if x_internal_token and x_internal_token == self.internal_token:
            return {"status": "success", "tools": self.agent.get_tools_info()}
        parts = parse_bearer_parts(authorization)
        if parts:
            if is_internal_bearer(parts, self.internal_token):
                return {"status": "success", "tools": self.agent.get_tools_info()}
            parsed = extract_user_password_session(parts, default_session="default")
            if parsed and self.verify_password(parsed[0], parsed[1]):
                return {"status": "success", "tools": self.agent.get_tools_info()}
        raise HTTPException(status_code=403, detail="认证失败")

    async def login(self, req: LoginRequest):
        if self.verify_password(req.user_id, req.password):
            logger.info("login success user=%s", req.user_id)
            return {"status": "success", "message": "登录成功"}
        logger.warning("login failed user=%s", req.user_id)
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    async def cancel_agent(self, req: CancelRequest, x_internal_token: str | None):
        self.verify_auth_or_token(req.user_id, req.password, x_internal_token)
        task_key = f"{req.user_id}#{req.session_id}"
        logger.info("cancel user=%s session=%s", req.user_id, req.session_id)
        await self.agent.cancel_task(task_key)
        return {"status": "success", "message": "已终止"}

    async def text_to_speech(self, req: TTSRequest, x_internal_token: str | None):
        self.verify_auth_or_token(req.user_id, req.password, x_internal_token)

        tts_text = req.text.strip()
        if not tts_text:
            raise HTTPException(status_code=400, detail="文本不能为空")
        if len(tts_text) > 4000:
            tts_text = tts_text[:4000]

        api_key = os.getenv("LLM_API_KEY", "")
        base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")
        tts_model = os.getenv("TTS_MODEL", "gemini-2.5-flash-preview-tts")
        tts_voice = req.voice or os.getenv("TTS_VOICE", "charon")

        if not api_key or not base_url:
            raise HTTPException(status_code=500, detail="TTS API 未配置")

        tts_url = f"{base_url}/audio/speech"

        async def audio_stream():
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    tts_url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": tts_model,
                        "input": tts_text,
                        "voice": tts_voice,
                        "response_format": "mp3",
                    },
                ) as resp:
                    if resp.status_code != 200:
                        error_body = await resp.aread()
                        raise HTTPException(
                            status_code=resp.status_code,
                            detail=f"TTS API 错误: {error_body.decode('utf-8', errors='replace')[:200]}",
                        )
                    async for chunk in resp.aiter_bytes(chunk_size=4096):
                        yield chunk

        return StreamingResponse(
            audio_stream(),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=tts_output.mp3"},
        )
