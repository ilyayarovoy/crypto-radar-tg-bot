import os
import json
import logging
from collections import defaultdict

import aiohttp
from dotenv import load_dotenv

from database.models import MarketSnapshotModel

load_dotenv()

OPENROUTER_API = os.getenv("OPEN_ROUTER_API")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openrouter/free"

logger = logging.getLogger(__name__)


# Системный промпт для дневного отчёта по монетам — отдельный от промпта обычного
# чата (тот лежит в system-promt-for-ai.txt), т.к. это разные задачи с разным форматом.
REPORT_SYSTEM_PROMPT = """Ты — финансовый аналитик-ассистент в Telegram-боте.
Тебе дают JSON: по каждой монете — временной ряд последних снапшотов
(цена, % изменения за 24ч, капитализация), от старых к новым — обычно
это данные за последние 7 дней, по одному снапшоту в день.

Проанализируй ДИНАМИКУ по каждой монете (растёт/падает/стоит на месте,
ускоряется ли движение, есть ли разворот тренда), а не просто последнее
значение. Сформируй краткий дневной отчёт на русском языке:
- по каждой монете 1-3 предложения с акцентом на тренд за период, используй
  эмодзи 📈/📉/➡️
- в конце — короткий общий вывод по настроению рынка в 1-2 предложениях

Не выдумывай цифры и события, которых нет в JSON. Если по какой-то монете
всего один снапшот — так и скажи, что истории пока недостаточно для тренда,
без домыслов."""


class AIService:

    @staticmethod
    def _load_chat_system_prompt(filename: str = "system-promt-for-ai.txt") -> str:
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError as error:
            raise FileNotFoundError(error)

    @staticmethod
    async def _call_ai(system_prompt: str, user_message: str, message_history: list = None) -> str:
        """
        Общая точка похода в OpenRouter. И обычный чат, и генерация отчёта идут
        через неё — чтобы не дублировать HTTP-логику, обработку ошибок и таймауты
        в двух местах.
        """
        if not OPENROUTER_API:
            logger.error("OPEN_ROUTER_API не задан в .env")
            return "ИИ временно недоступен: не настроен API-ключ."

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API}",
            "Content-Type": "application/json",
        }

        messages = [{"role": "system", "content": system_prompt}]

        if message_history:
            messages.extend(message_history)

        # ВАЖНО: раньше user_message принимался, но никогда не добавлялся в messages —
        # реальный вопрос/данные пользователя физически не долетали до ИИ.
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": OPENROUTER_MODEL,
            "messages": messages,
            "max_tokens": 1000,
        }

        timeout = aiohttp.ClientTimeout(total=60)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(OPENROUTER_URL, json=payload, headers=headers) as response:
                    result = await response.json()

                    if response.status == 200:
                        return result["choices"][0]["message"]["content"]

                    error_msg = result.get("error", {}).get("message", "неизвестная ошибка")
                    logger.error(f"Ошибка API ({response.status}): {error_msg}")
                    return "Извините, произошла ошибка. Попробуйте позже."

        except aiohttp.ClientConnectorError as e:
            logger.error(f"Ошибка подключения: {e}")
            return "Не могу подключиться к серверу. Проверьте интернет."

        except Exception as e:
            logger.error(f"Неожиданная ошибка: {type(e).__name__}: {e}")
            return "Произошла непредвиденная ошибка."

    # ---------- обычный чат ----------

    @staticmethod
    async def get_response_from_ai(user_message: str, message_history: list = None) -> str:
        """Ответ в обычном диалоге — системный промпт берётся из system-promt-for-ai.txt."""
        system_prompt = AIService._load_chat_system_prompt()
        return await AIService._call_ai(system_prompt, user_message, message_history)

    # ---------- отчёт по избранным монетам ----------

    @staticmethod
    def build_report_payload(snapshots: list[MarketSnapshotModel]) -> dict:
        """
        Группирует плоский список снапшотов (из ReporteService.get_market_snapshots)
        по монете и превращает в компактный временной ряд для ИИ.

        В каждую точку ряда кладём только то, что реально меняется и полезно для
        тренда (цена, % изменения, капа) — а не все 15 полей модели, иначе промпт
        раздувается в 7 раз на статичных данных (name, image, ath и т.д.).
        """
        grouped: dict[str, list[dict]] = defaultdict(list)

        for s in snapshots:
            grouped[s.coin_id].append({
                "timestamp": s.created_at.isoformat(),
                "price_usd": s.current_price,
                "change_24h_percent": s.price_change_percentage_24h,
                "market_cap": s.market_cap,
            })

        return dict(grouped)

    @staticmethod
    async def generate_market_report(snapshots: list[MarketSnapshotModel]) -> str:
        """Принимает снапшоты ОДНОГО юзера (по его избранным монетам) и возвращает текст отчёта."""
        if not snapshots:
            return "Пока нет рыночных данных по твоим монетам — попробуй чуть позже."

        payload = AIService.build_report_payload(snapshots)
        user_message = json.dumps(payload, ensure_ascii=False)

        return await AIService._call_ai(REPORT_SYSTEM_PROMPT, user_message)