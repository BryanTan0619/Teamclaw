import asyncio
from typing import Any, Callable

from langchain_core.messages import HumanMessage, ToolMessage

from logging_utils import get_logger
from system_models import SystemTriggerRequest

logger = get_logger("system_service")


class SystemService:
    def __init__(
        self,
        *,
        agent: Any,
        verify_internal_token: Callable[[str | None], None],
    ):
        self.agent = agent
        self.verify_internal_token = verify_internal_token

    async def system_trigger(self, req: SystemTriggerRequest, x_internal_token: str | None):
        self.verify_internal_token(x_internal_token)
        thread_id = f"{req.user_id}#{req.session_id}"
        config = {"configurable": {"thread_id": thread_id}}
        system_input = {
            "messages": [HumanMessage(content=req.text)],
            "trigger_source": "system",
            "enabled_tools": None,
            "user_id": req.user_id,
            "session_id": req.session_id,
        }

        async def wait_and_invoke():
            task_key = f"{req.user_id}#{req.session_id}"
            lock = await self.agent.get_thread_lock(thread_id)
            logger.info("Waiting for lock on %s ...", thread_id)
            async with lock:
                self.agent.set_thread_busy_source(thread_id, "system")
                logger.info("Acquired lock on %s, invoking graph ...", thread_id)
                try:
                    async for _ in self.agent.agent_app.astream_events(system_input, config, version="v2"):
                        pass
                    self.agent.add_pending_system_message(thread_id)
                    logger.info("Done for %s", thread_id)
                except asyncio.CancelledError:
                    logger.info("Cancelled for %s", thread_id)
                    try:
                        snapshot = await self.agent.agent_app.aget_state(config)
                        last_msgs = snapshot.values.get("messages", [])
                        if last_msgs:
                            last_msg = last_msgs[-1]
                            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                                tool_messages = [
                                    ToolMessage(
                                        content="⚠️ 系统调用被用户终止",
                                        tool_call_id=tc["id"],
                                    )
                                    for tc in last_msg.tool_calls
                                ]
                                await self.agent.agent_app.aupdate_state(config, {"messages": tool_messages})
                    except Exception:
                        pass
                except Exception as e:
                    logger.exception("Error for %s: %s", thread_id, e)
                finally:
                    self.agent.clear_thread_busy_source(thread_id)
                    self.agent.unregister_task(task_key)

        task_key = f"{req.user_id}#{req.session_id}"
        await self.agent.cancel_task(task_key)
        task = asyncio.create_task(wait_and_invoke())
        self.agent.register_task(task_key, task)
        return {"status": "received", "message": f"系统触发已收到，用户 {req.user_id}"}
