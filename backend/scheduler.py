import asyncio
import logging
from datetime import datetime
from agent import control_tv, control_cooler, control_ac, control_lamp, handle_user_request
from response_agent import make_response
from task_db import ScheduledTaskDBItem, get_due_tasks, delete_task, add_task, init_db, set_device_status, get_device_status
from assistant import VoiceAssistant
import aiosqlite
from dotenv import load_dotenv
load_dotenv()

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("log/scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

FUNCTION_MAP = {
    "control_tv": control_tv,
    "control_cooler": control_cooler,
    "control_ac": control_ac,
    "control_lamp": control_lamp,
}

class ScheduledTask:
    def __init__(self, db_item: ScheduledTaskDBItem):
        self.db_item = db_item

    async def run(self):
        func = FUNCTION_MAP.get(self.db_item.function_name)
        if not func:
            logger.error(f"❌ Unknown function name: {self.db_item.function_name}")
            return

        try:
            logger.info(f"Running task {self.db_item.id} → {self.db_item.function_name} at {datetime.now()} with args={self.db_item.args} kwargs={self.db_item.kwargs}")
            if hasattr(func, "ainvoke"):
                await func.ainvoke(self.db_item.kwargs)
            else:
                result = func(*self.db_item.args, **self.db_item.kwargs)
                if asyncio.iscoroutine(result):
                    await result
            logger.info(f"✅ Task {self.db_item.id} executed successfully.")
        except Exception as e:
            logger.exception(f"❌ Error running task {self.db_item.id}: {e}")


def get_device_name(function_name: str, kwargs: dict) -> str:
    device_map = {
        'control_tv': lambda kw: "TV",
        'control_cooler': lambda kw: "Cooler",
        'control_ac': lambda kw: {
            'room1': "AC_room1",
            'kitchen': "AC_kitchen"
        }.get(kw.get('room'), ""),
        'control_lamp': lambda kw: {
            'kitchen': "lamp_kitchen",
            'bathroom': "lamp_bathroom",
            'room1': "lamp_room1",
            'room2': "lamp_room2"
        }.get(kw.get('room'), ""),
    }
    return device_map.get(function_name, lambda _: "")(kwargs)


async def scheduler_loop():
    logger.info("🕒 Scheduler loop started.")
    while True:
        due_db_tasks = await get_due_tasks()
        for db_task in due_db_tasks:
            task = ScheduledTask(db_task)
            await task.run()

            action = db_task.kwargs.get('action', '')
            device_name = get_device_name(db_task.function_name, db_task.kwargs)

            if device_name:
                await set_device_status(device_name, action)

            await delete_task(db_task.id)
            logger.info(f"🗑️ Task {db_task.id} deleted after execution.")
        await asyncio.sleep(1)

async def schedule_task(function_name: str, run_at: datetime, args=None, kwargs=None):
    logger.info(f"📝 Scheduling task: {function_name} at {run_at} with args={args}, kwargs={kwargs}")
    await add_task(function_name, run_at, args=args, kwargs=kwargs)

async def handle_user_command(user_input: str):
    logger.info(f"🧠 Handling user input: '{user_input}'")
    commands = handle_user_request(user_input)
    logger.info(f"Parsed commands: {commands}")

    for command in commands:
        fn_name = command['function']
        args = command['args']
        run_at = command['scheduled_for']

        if fn_name in ['get_news', 'get_weather']:
            continue

        await schedule_task(fn_name, run_at, kwargs=args)
        logger.info(f"📅 Scheduled: {fn_name} at {run_at} with args={args}")

    logger.info(f"Commands: {commands}")
    
    for command in commands:
        run_at = command['scheduled_for']
        if isinstance(run_at, datetime):
            command['scheduled_for'] = run_at.isoformat()
        else:
            command['scheduled_for'] = str(run_at)

    response = make_response(commands)
    logger.info(f"Response: {response}")
    return response

async def async_listen_for_command(assistant: VoiceAssistant):
    logger.info("👂 Listening for wake word...")
    detected = await asyncio.to_thread(assistant.listen_for_wake_word)
    if detected:
        logger.info("🗣️ Wake word detected! Listening for command...")
        audio = await asyncio.to_thread(assistant.listen_for_command)
        command = await asyncio.to_thread(assistant.transcribe_command, audio)
        logger.info(f"📝 Transcribed command: {command}")
        return command
    logger.info("🔇 No wake word detected.")
    return None

async def get_all_device_statuses() -> dict:
    async with aiosqlite.connect('async_task_queue.db') as db:
        cursor = await db.execute('SELECT device_name, status FROM device_status')
        rows = await cursor.fetchall()
        return {device_name: status for device_name, status in rows}
