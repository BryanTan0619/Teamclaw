import aiosqlite


async def list_thread_ids_by_prefix(db_path: str, prefix: str) -> list[str]:
    """按 thread_id 前缀查询会话列表。"""
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT DISTINCT thread_id FROM checkpoints WHERE thread_id LIKE ? ORDER BY thread_id",
            (f"{prefix}%",),
        )
        rows = await cursor.fetchall()
    return [row[0] for row in rows]


async def delete_thread_records(db_path: str, thread_id: str) -> None:
    """删除指定 thread 在 checkpoints/writes 中的记录。"""
    async with aiosqlite.connect(db_path) as db:
        for table in ("checkpoints", "writes"):
            await db.execute(f"DELETE FROM {table} WHERE thread_id = ?", (thread_id,))
        await db.commit()


async def delete_thread_records_like(db_path: str, pattern: str) -> None:
    """按 LIKE 模式删除 checkpoints/writes 记录。"""
    async with aiosqlite.connect(db_path) as db:
        for table in ("checkpoints", "writes"):
            await db.execute(f"DELETE FROM {table} WHERE thread_id LIKE ?", (pattern,))
        await db.commit()
