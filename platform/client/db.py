import aiosqlite

async def init_db(db_path: str) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS processed_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                status TEXT CHECK(status IN ('PASSED', 'REJECTED')) NOT NULL,
                reason TEXT,
                inpaint_ratio REAL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS privacy_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                round_id INTEGER NOT NULL,
                epsilon_consumed REAL NOT NULL,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def log_file_status(db_path: str, filename: str, status: str, reason: str, inpaint_ratio: float) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO processed_files (filename, status, reason, inpaint_ratio) VALUES (?, ?, ?, ?)",
            (filename, status, reason, inpaint_ratio)
        )
        await db.commit()

async def log_epsilon(db_path: str, round_id: int, epsilon: float) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO privacy_logs (round_id, epsilon_consumed) VALUES (?, ?)",
            (round_id, epsilon)
        )
        await db.commit()

async def get_max_epsilon(db_path: str) -> float:
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT MAX(epsilon_consumed) FROM privacy_logs") as cursor:
            row = await cursor.fetchone()
            return row[0] if row and row[0] is not None else 0.0

async def get_recent_files(db_path: str, limit: int = 50) -> list:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, filename, status, reason, inpaint_ratio, processed_at FROM processed_files ORDER BY processed_at DESC LIMIT ?",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
