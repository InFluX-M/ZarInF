import aiosqlite
import pickle
import logging
from datetime import datetime

DB_PATH = "async_task_queue.db"

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("log/task_db.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScheduledTaskDBItem:
    def __init__(self, id_, function_name: str, run_at: datetime, args=None, kwargs=None):
        self.id = id_
        self.function_name = function_name
        self.run_at = run_at
        self.args = args or []
        self.kwargs = kwargs or {}

# --- Database Initialization ---
async def init_db():
    logger.info("🛠️ Initializing database...")
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

        await db.execute('''
            CREATE TABLE IF NOT EXISTS device_status (
                device_name TEXT PRIMARY KEY,
                status TEXT
            )
        ''')

        # Initialize all devices with 'off' status if not already in table
        devices = [
            "lamp_kitchen", "lamp_bathroom", "lamp_room1", "lamp_room2",
            "AC_room1", "AC_kitchen", "Cooler", "TV"
        ]
        for device in devices:
            await db.execute('''
                INSERT OR IGNORE INTO device_status (device_name, status)
                VALUES (?, ?)
            ''', (device, 'off'))

        await db.commit()
    logger.info("✅ Database initialized or already exists.")

# --- Task Management ---
async def add_task(function_name: str, run_at: datetime, args=None, kwargs=None):
    args = args or []
    kwargs = kwargs or {}
    logger.info(f"➕ Adding task: {function_name} at {run_at} with args={args}, kwargs={kwargs}")
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
    logger.info("✅ Task added to the database.")

async def get_due_tasks():
    now_iso = datetime.now().isoformat()
    logger.debug(f"⏰ Checking for tasks due at or before {now_iso}")
    async with aiosqlite.connect(DB_PATH) as db:
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
        if tasks:
            logger.info(f"📋 Retrieved {len(tasks)} due task(s).")
        return tasks

async def delete_task(task_id: int):
    logger.info(f"🗑️ Deleting task with ID: {task_id}")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        await db.commit()
    logger.info(f"✅ Task {task_id} deleted.")

# --- Device Status Management ---
async def set_device_status(device_name: str, new_status: str):
    logger.info(f"🔧 Setting device '{device_name}' to '{new_status}'")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'UPDATE device_status SET status = ? WHERE device_name = ?',
            (new_status, device_name)
        )
        await db.commit()
    logger.info(f"✅ Device '{device_name}' status updated to '{new_status}'")

async def get_device_status(device_name: str) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            'SELECT status FROM device_status WHERE device_name = ?',
            (device_name,)
        )
        row = await cursor.fetchone()
        if row:
            return row[0]
        logger.warning(f"⚠️ Device '{device_name}' not found.")
        return "unknown"