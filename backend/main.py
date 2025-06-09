import asyncio
from datetime import datetime
from agent import control_tv, control_cooler, control_ac, control_lamp, handle_user_request
from task_db import ScheduledTaskDBItem, get_due_tasks, delete_task, add_task, init_db
from assistant import VoiceAssistant
import os

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
            print(f"❌ Unknown function name: {self.db_item.function_name}")
            return

        if hasattr(func, "ainvoke"):
            await func.ainvoke(self.db_item.kwargs)
        else:
            result = func(*self.db_item.args, **self.db_item.kwargs)
            if asyncio.iscoroutine(result):
                await result

async def scheduler_loop():
    while True:
        due_db_tasks = await get_due_tasks()
        for db_task in due_db_tasks:
            task = ScheduledTask(db_task)
            try:
                await task.run()
            except Exception as e:
                print(f"❌ Error running task {db_task.id}: {e}")
            await delete_task(db_task.id)
        await asyncio.sleep(1)

async def schedule_task(function_name: str, run_at: datetime, args=None, kwargs=None):
    await add_task(function_name, run_at, args=args, kwargs=kwargs)

async def handle_user_command(user_input: str):
    commands = handle_user_request(user_input)
    scheduled = []

    for fn_name, args, run_at in commands:
        await schedule_task(fn_name, run_at, kwargs=args)
        scheduled.append((fn_name, run_at))

    return scheduled

async def async_listen_for_command(assistant: VoiceAssistant):
    print("Listening for wake word...")
    # Run sync/blocking methods in a thread to avoid blocking the event loop
    detected = await asyncio.to_thread(assistant.listen_for_wake_word)
    if detected:
        print("Wake word detected! Listening for command...")
        audio = await asyncio.to_thread(assistant.listen_for_command)
        command = await asyncio.to_thread(assistant.transcribe_command, audio)
        print(f"Command: {command}")
        return command
    return None

async def main():
    await init_db()
    asyncio.create_task(scheduler_loop())
    print("📡 Scheduler running...")

    assistant = VoiceAssistant(os.getenv("ACCESS_KEY"), os.getenv("KEYWORD_PATHS"))

    try:
        while True:
            print("👂 Listening for wake word...")
            await assistant.detect_wake_word()
            print("🎤 Wake word detected!")

            audio = await assistant.async_listen_for_command()
            command = await assistant.async_transcribe_command(audio)
            print(f"🧠 Command: {command}")

            await handle_user_command(command)

            if "bye" in command.lower():
                print("👋 Exiting...")
                break

            await asyncio.sleep(0.1)

    except KeyboardInterrupt:
        print("🛑 Interrupted by user.")
    finally:
        assistant.close()

if __name__ == "__main__":
    asyncio.run(main())