import asyncio
import logging
import aiohttp
import os
from dotenv import load_dotenv

from database import session_maker
from service.report_service import ReporteService

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")

logger = logging.getLogger(__name__)


class CoinGekoService:

    @staticmethod
    async def get_coin_id_from_name(coins_list: list[str]):
        headers = {"X-CMC_PRO_API_KEY": API_KEY}
        coins = []
        async with aiohttp.ClientSession() as session:
            for coin_name in coins_list:
                async with session.get(f"{BASE_URL}/v3/search?query={coin_name}", headers=headers) as response:
                    data = await response.json()
                    if response.status != 200:
                        # Исправлено: одинарные кавычки внутри f-строки
                        raise Exception(f"Error {data['status']}")

                    if "coins" in data and len(data["coins"]) > 0:
                        coins.append(data["coins"][0]["id"])
                    else:
                        logger.warning(f"Монета '{coin_name}' не найдена в CoinGecko")
        return coins

    @staticmethod
    async def market_data_for_coin(coins_list: list[str]):
        headers = {"X-CMC_PRO_API_KEY": API_KEY}

        async with aiohttp.ClientSession() as session:
            for coin_id in coins_list:
                async with session.get(f"{BASE_URL}/v3/coins/markets?vs_currency=usd&ids={coin_id}",
                                       headers=headers) as response:
                    data = await response.json()
                    if response.status != 200:
                        # Исправлено: одинарные кавычки внутри f-строки
                        raise Exception(f"Error {data['status']}")

                    if not data:
                        logger.warning(
                        "Данные для монеты '{coin_id}' не найдены")
                        continue

                    coin_data = data[0]
                    name = coin_data.get("name")
                    image = coin_data.get("image")
                    current_price = coin_data.get("current_price")
                    market_cap = coin_data.get("market_cap")
                    fully_diluted_valuation = coin_data.get("fully_diluted_valuation")
                    total_volume = coin_data.get("total_volume")
                    high_24h = coin_data.get("high_24h")
                    low_24h = coin_data.get("low_24h")
                    price_change_24h = coin_data.get("price_change_24h")
                    price_change_percentage_24h = coin_data.get("price_change_percentage_24h")
                    market_cap_change_24h = coin_data.get("market_cap_change_24h")
                    market_cap_change_percentage_24h = coin_data.get("market_cap_change_percentage_24h")
                    circulating_supply = coin_data.get("circulating_supply")
                    total_supply = coin_data.get("total_supply")
                    ath = coin_data.get("ath")

                async with session_maker() as db_session:
                    report_service = ReporteService(db_session)
                    await report_service.add_new_report_from_coingeko(
                        coin_id=coin_id,
                        name=name,
                        image=image,
                        current_price=current_price,
                        market_cap=market_cap,
                        fully_diluted_valuation=fully_diluted_valuation,
                        total_volume=total_volume,
                        high_24h=high_24h,
                        low_24h=low_24h,
                        price_change_24h=price_change_24h,
                        price_change_percentage_24h=price_change_percentage_24h,
                        market_cap_change_24h=market_cap_change_24h,
                        market_cap_change_percentage_24h=market_cap_change_percentage_24h,
                        circulating_supply=circulating_supply,
                        total_supply=total_supply,
                        ath=ath
                    )