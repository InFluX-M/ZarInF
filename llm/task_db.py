import aiosqlite
import pickle
from datetime import datetime

DB_PATH = "async_task_queue.db"

class ScheduledTaskDBItem:
    def __init__(self, id_, function_name: str, run_at: datetime, args=None, kwargs=None):
        self.id = id_
        self.function_name = function_name
        self.run_at = run_at
        self.args = args or []
        self.kwargs = kwargs or {}

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_at TEXT,
                function_name TEXT,
                args_blob BLOB,
                kwargs_blob BLOB
            )
        ''')
        await db.commit()

async def add_task(function_name: str, run_at: datetime, args=None, kwargs=None):
    args = args or []
    kwargs = kwargs or {}
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT INTO tasks (run_at, function_name, args_blob, kwargs_blob) VALUES (?, ?, ?, ?)',
            (
                run_at.isoformat(),
                function_name,
                pickle.dumps(args),
                pickle.dumps(kwargs),
            )
        )
        await db.commit()

async def get_due_tasks():
    async with aiosqlite.connect(DB_PATH) as db:
        now_iso = datetime.now().isoformat()
        cursor = await db.execute(
            'SELECT id, run_at, function_name, args_blob, kwargs_blob FROM tasks WHERE run_at <= ?',
            (now_iso,)
        )
        rows = await cursor.fetchall()
        tasks = []
        for row in rows:
            id_, run_at, fn_name, args_blob, kwargs_blob = row
            task = ScheduledTaskDBItem(
                id_=id_,
                function_name=fn_name,
                run_at=datetime.fromisoformat(run_at),
                args=pickle.loads(args_blob),
                kwargs=pickle.loads(kwargs_blob),
            )
            tasks.append(task)
        return tasks

async def delete_task(task_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        await db.commit()
