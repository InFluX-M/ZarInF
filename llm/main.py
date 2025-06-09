import asyncio
from datetime import datetime, timedelta
from task_db import ScheduledTask, init_db, add_task, get_due_tasks, delete_task

# --- Example tasks ---
def turn_on_lamp():
    print(f"[{datetime.now()}] Lamp turned ON!")

async def notify_user(msg):
    print(f"[{datetime.now()}] Notification: {msg}")

# --- Scheduler Loop ---
async def scheduler_loop():
    while True:
        due_tasks = await get_due_tasks()
        for task_id, task in due_tasks:
            try:
                await task.run()
            except Exception as e:
                print(f"Error running task {task_id}: {e}")
            await delete_task(task_id)
        await asyncio.sleep(1)

# --- Agent Command Example ---
async def handle_user_command(user_input: str):
    pass

# --- Entrypoint ---
async def main():
    await init_db()
    asyncio.create_task(scheduler_loop())
    print("Async scheduler started.")

    # Simulated inputs
    print(await handle_user_command("lamp in 2 hours"))
    print(await handle_user_command("notify me"))

    while True:
        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
