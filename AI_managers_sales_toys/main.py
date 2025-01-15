import asyncio
from work_with_telegram.main import main as main_tg
from work_with_instagram.main import main as main_inst


async def run_services():
    telegram_task = asyncio.create_task(main_tg())
    instagram_task = asyncio.create_task(main_inst())

    await asyncio.gather(telegram_task, instagram_task)


if __name__ == '__main__':
    asyncio.run(run_services())