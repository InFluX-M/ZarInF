# task_db.py

import aiosqlite
import pickle
from datetime import datetime
from typing import Callable

DB_PATH = "async_task_queue.db"

class ScheduledTask:
    def __init__(self, function: Callable, run_at: datetime, args=None, kwargs=None):
        self.function = function
        self.run_at = run_at
        self.args = args or []
        self.kwargs = kwargs or {}

    async def run(self):
        if callable(self.function):
            if hasattr(self.function, "__call__"):
                if hasattr(self.function, "__code__") and self.function.__code__.co_flags & 0x80:
                    await self.function(*self.args, **self.kwargs)
                else:
                    self.function(*self.args, **self.kwargs)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_at TEXT,
                function_blob BLOB,
                args_blob BLOB,
                kwargs_blob BLOB
            )
        ''')
        await db.commit()

async def add_task(task: ScheduledTask):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT INTO tasks (run_at, function_blob, args_blob, kwargs_blob) VALUES (?, ?, ?, ?)',
            (
                task.run_at.isoformat(),
                pickle.dumps(task.function),
                pickle.dumps(task.args),
                pickle.dumps(task.kwargs),
            )
        )
        await db.commit()

async def get_due_tasks():
    async with aiosqlite.connect(DB_PATH) as db:
        now_iso = datetime.now().isoformat()
        cursor = await db.execute(
            'SELECT id, run_at, function_blob, args_blob, kwargs_blob FROM tasks WHERE run_at <= ?',
            (now_iso,)
        )
        rows = await cursor.fetchall()
        tasks = []
        for row in rows:
            id_, run_at, fn_blob, args_blob, kwargs_blob = row
            task = ScheduledTask(
                function=pickle.loads(fn_blob),
                run_at=datetime.fromisoformat(run_at),
                args=pickle.loads(args_blob),
                kwargs=pickle.loads(kwargs_blob)
            )
            tasks.append((id_, task))
        return tasks

async def delete_task(task_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        await db.commit()
