import aiosqlite


async def init_group_db(group_db_path: str) -> None:
    """初始化群聊数据库表结构。"""
    async with aiosqlite.connect(group_db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                group_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                owner TEXT NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS group_members (
                group_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL DEFAULT 'default',
                is_agent INTEGER NOT NULL DEFAULT 1,
                joined_at REAL NOT NULL,
                PRIMARY KEY (group_id, user_id, session_id),
                FOREIGN KEY (group_id) REFERENCES groups(group_id) ON DELETE CASCADE
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS group_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT NOT NULL,
                sender TEXT NOT NULL,
                sender_session TEXT NOT NULL DEFAULT '',
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                FOREIGN KEY (group_id) REFERENCES groups(group_id) ON DELETE CASCADE
            )
        """)
        await db.commit()


async def list_group_member_targets(group_db_path: str, group_id: str) -> list[tuple[str, str, int]]:
    """查询群成员（广播用途）。"""
    async with aiosqlite.connect(group_db_path) as db:
        cursor = await db.execute(
            "SELECT user_id, session_id, is_agent FROM group_members WHERE group_id = ?",
            (group_id,),
        )
        return await cursor.fetchall()


async def create_group_with_members(
    group_db_path: str,
    *,
    group_id: str,
    name: str,
    owner: str,
    created_at: float,
    members: list[dict],
) -> None:
    async with aiosqlite.connect(group_db_path) as db:
        await db.execute(
            "INSERT INTO groups (group_id, name, owner, created_at) VALUES (?, ?, ?, ?)",
            (group_id, name, owner, created_at),
        )
        await db.execute(
            "INSERT INTO group_members (group_id, user_id, session_id, is_agent, joined_at) VALUES (?, ?, ?, 0, ?)",
            (group_id, owner, "default", created_at),
        )
        for m in members:
            m_uid = m.get("user_id", "")
            m_sid = m.get("session_id", "default")
            if m_uid:
                await db.execute(
                    "INSERT OR IGNORE INTO group_members (group_id, user_id, session_id, is_agent, joined_at) VALUES (?, ?, ?, 1, ?)",
                    (group_id, m_uid, m_sid, created_at),
                )
        await db.commit()


async def list_groups_for_user(group_db_path: str, user_id: str) -> list[dict]:
    async with aiosqlite.connect(group_db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT g.group_id, g.name, g.owner, g.created_at,
                   (SELECT COUNT(*) FROM group_members WHERE group_id = g.group_id) as member_count,
                   (SELECT COUNT(*) FROM group_messages WHERE group_id = g.group_id) as message_count
            FROM groups g
            WHERE g.owner = ? OR g.group_id IN (
                SELECT group_id FROM group_members WHERE user_id = ?
            )
            ORDER BY g.created_at DESC
            """,
            (user_id, user_id),
        )
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_group(group_db_path: str, group_id: str) -> dict | None:
    async with aiosqlite.connect(group_db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM groups WHERE group_id = ?", (group_id,))
        row = await cursor.fetchone()
    return dict(row) if row else None


async def list_group_members(group_db_path: str, group_id: str) -> list[dict]:
    async with aiosqlite.connect(group_db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT user_id, session_id, is_agent, joined_at FROM group_members WHERE group_id = ?",
            (group_id,),
        )
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def list_recent_group_messages(group_db_path: str, group_id: str, limit: int = 100) -> list[dict]:
    async with aiosqlite.connect(group_db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, sender, sender_session, content, timestamp FROM group_messages WHERE group_id = ? ORDER BY id DESC LIMIT ?",
            (group_id, limit),
        )
        rows = await cursor.fetchall()
    messages = [dict(r) for r in rows]
    messages.reverse()
    return messages


async def list_group_messages_after(
    group_db_path: str,
    group_id: str,
    after_id: int,
    limit: int = 200,
) -> list[dict]:
    async with aiosqlite.connect(group_db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, sender, sender_session, content, timestamp FROM group_messages WHERE group_id = ? AND id > ? ORDER BY id ASC LIMIT ?",
            (group_id, after_id, limit),
        )
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def group_exists(group_db_path: str, group_id: str) -> bool:
    async with aiosqlite.connect(group_db_path) as db:
        cursor = await db.execute("SELECT group_id FROM groups WHERE group_id = ?", (group_id,))
        return (await cursor.fetchone()) is not None


async def insert_group_message(
    group_db_path: str,
    *,
    group_id: str,
    sender: str,
    sender_session: str,
    content: str,
    timestamp: float,
) -> int:
    async with aiosqlite.connect(group_db_path) as db:
        cursor = await db.execute(
            "INSERT INTO group_messages (group_id, sender, sender_session, content, timestamp) VALUES (?, ?, ?, ?, ?)",
            (group_id, sender, sender_session, content, timestamp),
        )
        msg_id = cursor.lastrowid
        await db.commit()
    return msg_id


async def get_group_owner(group_db_path: str, group_id: str) -> str | None:
    async with aiosqlite.connect(group_db_path) as db:
        cursor = await db.execute("SELECT owner FROM groups WHERE group_id = ?", (group_id,))
        row = await cursor.fetchone()
    return row[0] if row else None


async def update_group_name(group_db_path: str, group_id: str, name: str) -> None:
    async with aiosqlite.connect(group_db_path) as db:
        await db.execute("UPDATE groups SET name = ? WHERE group_id = ?", (name, group_id))
        await db.commit()


async def add_group_member(
    group_db_path: str,
    *,
    group_id: str,
    user_id: str,
    session_id: str,
    joined_at: float,
) -> None:
    async with aiosqlite.connect(group_db_path) as db:
        await db.execute(
            "INSERT OR IGNORE INTO group_members (group_id, user_id, session_id, is_agent, joined_at) VALUES (?, ?, ?, 1, ?)",
            (group_id, user_id, session_id, joined_at),
        )
        await db.commit()


async def remove_group_member(
    group_db_path: str,
    *,
    group_id: str,
    user_id: str,
    session_id: str,
) -> None:
    async with aiosqlite.connect(group_db_path) as db:
        await db.execute(
            "DELETE FROM group_members WHERE group_id = ? AND user_id = ? AND session_id = ?",
            (group_id, user_id, session_id),
        )
        await db.commit()


async def delete_group(group_db_path: str, group_id: str) -> None:
    async with aiosqlite.connect(group_db_path) as db:
        await db.execute("DELETE FROM group_messages WHERE group_id = ?", (group_id,))
        await db.execute("DELETE FROM group_members WHERE group_id = ?", (group_id,))
        await db.execute("DELETE FROM groups WHERE group_id = ?", (group_id,))
        await db.commit()
