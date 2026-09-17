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
        for coin_name in coins_list:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{BASE_URL}/v3/search?query={coin_name}", headers=headers) as response:
                    data = await response.json()
                    if response.status != 200:
                        raise Exception(f"Error {response.status}")

                    # CoinGecko возвращает структуру {"coins": [...], "exchanges": [...]}
                    if "coins" in data and len(data["coins"]) > 0:
                        coins.append(data["coins"][0]["id"])
                    else:
                        logger.warning(f"Монета '{coin_name}' не найдена в CoinGecko")
        return coins

    @staticmethod
    async def market_data_for_coin(coins_list: list[str]):
        headers = {"X-CMC_PRO_API_KEY": API_KEY}

        coin_id = "solana"

        for coin_id in coins_list:

            async with aiohttp.ClientSession() as session:
                async with session.get(f"{BASE_URL}/v3/coins/markets?vs_currency=usd&ids={coin_id}", headers=headers) as response:
                    data = await response.json()
                    if response.status != 200:
                        raise Exception(f"Error {data["status"]}")
                    name = data[0]["name"]
                    image = data[0]["image"]
                    current_price = data[0]["current_price"]
                    market_cap = data[0]["market_cap"]
                    fully_diluted_valuation = data[0]["fully_diluted_valuation"]
                    total_volume = data[0]["total_volume"]
                    high_24h = data[0]["high_24h"]
                    low_24h = data[0]["low_24h"]
                    price_change_24h = data[0]["price_change_24h"]
                    price_change_percentage_24h = data[0]["price_change_percentage_24h"]
                    market_cap_change_24h = data[0]["market_cap_change_24h"]
                    market_cap_change_percentage_24h = data[0]["market_cap_change_percentage_24h"]
                    circulating_supply = data[0]["circulating_supply"]
                    total_supply = data[0]["total_supply"]
                    ath = data[0]["ath"]
            async with session_maker() as session:
                report_service = ReporteService(session)
                new_data = await report_service.add_new_report_from_coingeko(
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







