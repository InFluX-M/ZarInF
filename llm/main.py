import asyncio
from datetime import datetime
from agent import control_tv, control_cooler, control_ac, control_lamp, handle_user_request
from task_db import ScheduledTaskDBItem, get_due_tasks, delete_task, add_task, init_db

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

async def main():
    await init_db()
    asyncio.create_task(scheduler_loop())
    print("📡 Async scheduler running...")

    # Example user commands
    print(await handle_user_command("If Elcasico between Real and Barca exists, turn on the TV in 1 minutes and i have another task also turn on kitchen lamp in 30 seconds."))
    print(await handle_user_command("Turn on the AC in room1 if temperature is over 30 now"))

    while True:
        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
