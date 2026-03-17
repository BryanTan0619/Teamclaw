import asyncio
import json
from typing import Any, Callable

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from auth_utils import extract_user_password_session, is_internal_bearer, parse_bearer_parts
from openai_models import ChatCompletionRequest, ChatMessage, OpenAIExecutionContext
from openai_protocol import OpenAIProtocolHelper


class OpenAIChatService:
    def __init__(
        self,
        *,
        internal_token: str,
        verify_password: Callable[[str, str], bool],
        agent: Any,
        extract_text: Callable[[Any], str],
        build_human_message: Callable[[str, list[str] | None, list[dict] | None, list[dict] | None], HumanMessage],
    ):
        self.internal_token = internal_token
        self.verify_password = verify_password
        self.agent = agent
        self.extract_text = extract_text
        self.protocol = OpenAIProtocolHelper(build_human_message=build_human_message)

    def openai_msg_to_human_message(self, msg: ChatMessage) -> HumanMessage:
        return self.protocol.openai_msg_to_human_message(msg)

    def make_completion_id(self) -> str:
        return self.protocol.make_completion_id()

    def make_openai_response(
        self,
        content: str,
        model: str = "teambot",
        finish_reason: str = "stop",
        tool_calls: list[dict] | None = None,
    ) -> dict:
        return self.protocol.make_openai_response(
            content,
            model=model,
            finish_reason=finish_reason,
            tool_calls=tool_calls,
        )

    def make_openai_chunk(
        self,
        content: str = "",
        model: str = "teambot",
        finish_reason: str | None = None,
        completion_id: str = "",
        meta: dict | None = None,
    ) -> str:
        return self.protocol.make_openai_chunk(
            completion_id=completion_id,
            content=content,
            model=model,
            finish_reason=finish_reason,
            meta=meta,
        )

    def extract_external_tool_names(self, tools: list[dict] | None) -> set[str]:
        return self.protocol.extract_external_tool_names(tools)

    def format_tool_calls_for_openai(self, ai_msg: AIMessage, external_names: set[str]) -> list[dict] | None:
        return self.protocol.format_tool_calls_for_openai(ai_msg, external_names)

    def auth_openai_request(self, req: ChatCompletionRequest, auth_header: str | None):
        """从 OpenAI 请求中提取认证信息并验证。"""
        user_id = req.user
        password = req.password
        session_override = None

        parts = parse_bearer_parts(auth_header)
        if parts:
            if is_internal_bearer(parts, self.internal_token):
                if len(parts) >= 3:
                    return parts[1], True, parts[2]
                if len(parts) == 2:
                    return parts[1], True, None
                return user_id or "system", True, None

            parsed = extract_user_password_session(parts, default_session="")
            if parsed:
                user_id, password, session_override = parsed

        if not user_id or not password:
            return None, False, None
        if not self.verify_password(user_id, password):
            return None, False, None
        return user_id, True, session_override

    def _build_input_messages(self, req: ChatCompletionRequest):
        input_messages = []
        last_user_msg = None

        trailing_tool_msgs = []
        i = len(req.messages) - 1
        while i >= 0:
            msg = req.messages[i]
            if msg.role == "tool":
                trailing_tool_msgs.insert(0, msg)
                i -= 1
            elif msg.role == "assistant" and msg.tool_calls and trailing_tool_msgs:
                i -= 1
            else:
                break

        if trailing_tool_msgs:
            tool_result_messages = []
            for tmsg in trailing_tool_msgs:
                tool_result_messages.append(
                    ToolMessage(
                        content=tmsg.content if isinstance(tmsg.content, str) else json.dumps(tmsg.content, ensure_ascii=False),
                        tool_call_id=tmsg.tool_call_id or "",
                        name=tmsg.name or "",
                    )
                )
            return tool_result_messages

        system_parts = []
        for msg in req.messages:
            if msg.role == "system" and msg.content:
                system_parts.append(msg.content if isinstance(msg.content, str) else str(msg.content))

        for msg in reversed(req.messages):
            if msg.role == "user":
                last_user_msg = msg
                break
        if not last_user_msg:
            raise HTTPException(status_code=400, detail="messages 中缺少 user 或 tool 消息")

        human_msg = self.openai_msg_to_human_message(last_user_msg)
        if system_parts:
            sys_text = "\n".join(system_parts)
            if isinstance(human_msg.content, list):
                human_msg.content.insert(0, {"type": "text", "text": f"[来自调度方的指令]\n{sys_text}\n\n---\n"})
            else:
                human_msg.content = f"[来自调度方的指令]\n{sys_text}\n\n---\n{human_msg.content}"
        input_messages = [human_msg]
        return input_messages

    async def _patch_cancelled_tool_calls(self, config: dict) -> None:
        try:
            snapshot = await self.agent.agent_app.aget_state(config)
            last_msgs = snapshot.values.get("messages", [])
            if last_msgs:
                last_msg_item = last_msgs[-1]
                if hasattr(last_msg_item, "tool_calls") and last_msg_item.tool_calls:
                    tool_messages = [
                        ToolMessage(
                            content="⚠️ 工具调用被用户终止",
                            tool_call_id=tc["id"],
                        )
                        for tc in last_msg_item.tool_calls
                    ]
                    await self.agent.agent_app.aupdate_state(config, {"messages": tool_messages})
        except Exception:
            pass

    async def _run_non_stream(
        self,
        ctx: OpenAIExecutionContext,
    ):
        task_key = f"{ctx.user_id}#{ctx.session_id}"
        await self.agent.cancel_task(task_key)

        async def non_stream_worker():
            async with ctx.thread_lock:
                self.agent.set_thread_busy_source(ctx.thread_id, "user")
                try:
                    return await self.agent.agent_app.ainvoke(ctx.user_input, ctx.config)
                finally:
                    self.agent.clear_thread_busy_source(ctx.thread_id)

        task = asyncio.create_task(non_stream_worker())
        self.agent.register_task(task_key, task)
        try:
            result = await task
        except asyncio.CancelledError:
            await self._patch_cancelled_tool_calls(ctx.config)
            return self.make_openai_response("⚠️ 已终止", model=ctx.model_name)
        finally:
            self.agent.unregister_task(task_key)

        last_msg = result["messages"][-1]
        ext_tool_calls = self.format_tool_calls_for_openai(last_msg, ctx.external_tool_names)
        if ext_tool_calls:
            return self.make_openai_response(
                self.extract_text(last_msg.content), model=ctx.model_name, tool_calls=ext_tool_calls
            )

        reply = self.extract_text(last_msg.content)
        return self.make_openai_response(reply, model=ctx.model_name)

    async def _run_stream(
        self,
        ctx: OpenAIExecutionContext,
    ):
        task_key = f"{ctx.user_id}#{ctx.session_id}"
        await self.agent.cancel_task(task_key)

        queue: asyncio.Queue[str | None] = asyncio.Queue()
        completion_id = self.make_completion_id()

        async def stream_worker():
            collected_tokens = []
            chatbot_round = 0
            active_tool_names = []
            async with ctx.thread_lock:
                self.agent.set_thread_busy_source(ctx.thread_id, "user")
                try:
                    await queue.put(self.make_openai_chunk("", model=ctx.model_name, completion_id=completion_id))

                    async for event in self.agent.agent_app.astream_events(ctx.user_input, ctx.config, version="v2"):
                        kind = event.get("event", "")
                        ev_name = event.get("name", "")

                        if kind == "on_chain_start" and ev_name == "chatbot":
                            chatbot_round += 1
                            if chatbot_round > 1:
                                await queue.put(self.make_openai_chunk(
                                    model=ctx.model_name,
                                    completion_id=completion_id,
                                    meta={"type": "ai_start", "round": chatbot_round},
                                ))
                        elif kind == "on_chain_start" and ev_name == "tools":
                            active_tool_names = []
                            await queue.put(self.make_openai_chunk(
                                model=ctx.model_name,
                                completion_id=completion_id,
                                meta={"type": "tools_start"},
                            ))
                        elif kind == "on_chain_end" and ev_name == "tools":
                            await queue.put(self.make_openai_chunk(
                                model=ctx.model_name,
                                completion_id=completion_id,
                                meta={"type": "tools_end", "tools": active_tool_names},
                            ))
                        elif kind == "on_tool_start":
                            tool_name = ev_name
                            if tool_name not in ctx.external_tool_names:
                                active_tool_names.append(tool_name)
                                await queue.put(self.make_openai_chunk(
                                    model=ctx.model_name,
                                    completion_id=completion_id,
                                    meta={"type": "tool_start", "name": tool_name},
                                ))
                        elif kind == "on_tool_end":
                            tool_name = ev_name
                            if tool_name not in ctx.external_tool_names:
                                output = event.get("data", {}).get("output", "")
                                if hasattr(output, "content"):
                                    output = output.content
                                output_str = str(output)[:200] if output else ""
                                await queue.put(self.make_openai_chunk(
                                    model=ctx.model_name,
                                    completion_id=completion_id,
                                    meta={"type": "tool_end", "name": tool_name, "result": output_str},
                                ))
                        elif kind == "on_chat_model_stream":
                            chunk = event.get("data", {}).get("chunk")
                            if chunk and hasattr(chunk, "content") and chunk.content:
                                text = self.extract_text(chunk.content)
                                if text:
                                    collected_tokens.append(text)
                                    await queue.put(self.make_openai_chunk(
                                        text, model=ctx.model_name, completion_id=completion_id
                                    ))

                    snapshot = await self.agent.agent_app.aget_state(ctx.config)
                    last_msgs = snapshot.values.get("messages", [])
                    if last_msgs:
                        last_msg_item = last_msgs[-1]
                        ext_tool_calls = self.format_tool_calls_for_openai(last_msg_item, ctx.external_tool_names)
                        if ext_tool_calls:
                            await queue.put(self.protocol.make_tool_calls_chunk(
                                completion_id=completion_id,
                                model=ctx.model_name,
                                tool_calls=ext_tool_calls,
                            ))
                            await queue.put("data: [DONE]\n\n")
                            return

                    await queue.put(self.make_openai_chunk(
                        "", model=ctx.model_name, finish_reason="stop", completion_id=completion_id
                    ))
                    await queue.put("data: [DONE]\n\n")
                except asyncio.CancelledError:
                    await self._patch_cancelled_tool_calls(ctx.config)
                    partial_text = "".join(collected_tokens)
                    if partial_text:
                        partial_text += "\n\n⚠️ （回复被用户终止）"
                        partial_msg = AIMessage(content=partial_text)
                        await self.agent.agent_app.aupdate_state(ctx.config, {"messages": [partial_msg]})
                    await queue.put(self.make_openai_chunk(
                        "\n\n⚠️ 已终止思考", model=ctx.model_name, completion_id=completion_id
                    ))
                    await queue.put(self.make_openai_chunk(
                        "", model=ctx.model_name, finish_reason="stop", completion_id=completion_id
                    ))
                    await queue.put("data: [DONE]\n\n")
                except Exception as e:
                    await queue.put(self.make_openai_chunk(
                        f"\n❌ 响应异常: {str(e)}", model=ctx.model_name, completion_id=completion_id
                    ))
                    await queue.put(self.make_openai_chunk(
                        "", model=ctx.model_name, finish_reason="stop", completion_id=completion_id
                    ))
                    await queue.put("data: [DONE]\n\n")
                finally:
                    self.agent.clear_thread_busy_source(ctx.thread_id)
                    await queue.put(None)
                    self.agent.unregister_task(task_key)

        task = asyncio.create_task(stream_worker())
        self.agent.register_task(task_key, task)

        async def event_generator():
            while True:
                item = await queue.get()
                if item is None:
                    break
                yield item

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    async def handle_chat_completions(
        self,
        req: ChatCompletionRequest,
        authorization: str | None,
    ):
        user_id, authenticated, session_override = self.auth_openai_request(req, authorization)
        if not authenticated:
            raise HTTPException(status_code=401, detail="认证失败")

        session_id = session_override or req.session_id or "default"
        thread_id = f"{user_id}#{session_id}"
        config = {"configurable": {"thread_id": thread_id}}

        external_tool_names = self.extract_external_tool_names(req.tools)
        input_messages = self._build_input_messages(req)

        user_input = {
            "messages": input_messages,
            "trigger_source": "user",
            "enabled_tools": req.enabled_tools,
            "user_id": user_id,
            "session_id": session_id,
            "external_tools": req.tools,
        }

        model_name = req.model or "teambot"
        thread_lock = await self.agent.get_thread_lock(thread_id)
        ctx = OpenAIExecutionContext(
            user_id=user_id,
            session_id=session_id,
            thread_id=thread_id,
            config=config,
            user_input=user_input,
            model_name=model_name,
            external_tool_names=external_tool_names,
            thread_lock=thread_lock,
        )

        if not req.stream:
            return await self._run_non_stream(ctx)

        return await self._run_stream(ctx)

    def list_models(self) -> dict:
        return self.protocol.list_models_payload()
