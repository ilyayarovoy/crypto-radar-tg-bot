import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from tg_bot.handlers import start_handler, favorite_coin_handler, get_report, help_handler, alert_handler
from jobs.daily_report_job import send_daily_reports
from jobs.check_alerts_job import check_price_alerts

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")

if not TG_BOT_TOKEN:
    raise ValueError("TG_BOT_TOKEN не найден в .env файле")


async def main():
    bot = Bot(
        token=TG_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()

    # Регистрируем роутеры
    dp.include_router(start_handler.router)
    dp.include_router(favorite_coin_handler.router)
    dp.include_router(get_report.router)
    dp.include_router(help_handler.router)
    dp.include_router(alert_handler.router)

    # Настраиваем scheduler для ежедневных отчётов в 9:00
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(
        send_daily_reports,
        CronTrigger(hour=9, minute=0),
        args=[bot]
    )

    # Настраиваем scheduler для проверки алертов каждые 10 минут
    scheduler.add_job(
        check_price_alerts,
        CronTrigger(minute='*/10'),
        args=[bot]
    )

    scheduler.start()

    logger.info("Бот запущен и готов к работе!")
    logger.info("Ежедневные отчёты будут отправляться в 9:00 МСК")
    logger.info("Проверка ценовых алертов каждые 10 минут")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        scheduler.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
