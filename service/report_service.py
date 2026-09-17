import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from database.models import MarketSnapshotModel
from database import session_maker

logger = logging.getLogger(__name__)




class ReporteService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_new_report_from_coingeko(self,
            coin_id: str,
            name: str,
            image: str,
            current_price: float,
            market_cap: float,
            fully_diluted_valuation: float,
            total_volume: float,
            high_24h: float,
            low_24h: float,
            price_change_24h: float,
            price_change_percentage_24h: float,
            market_cap_change_24h: float,
            market_cap_change_percentage_24h: float,
            circulating_supply: float,
            total_supply: float,
            ath: float

    ):
        new_data = MarketSnapshotModel(
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

        self.session.add(new_data)
        await self.session.commit()
        await self.session.refresh(new_data)
        logger.info(f"{new_data.name}")
        return new_data

    async def get_market_snapshots(
        self, coin_list: list[str], limit_per_coin: int = 7
    ) -> list[MarketSnapshotModel]:
        """
        Возвращает до `limit_per_coin` последних снапшотов для КАЖДОЙ монеты из
        coin_list — одним запросом (без цикла по монетам).

        Механика та же, что и раньше: ROW_NUMBER() нумерует снапшоты внутри
        каждой монеты (PARTITION BY coin_id) от самого свежего. Раньше брали
        только rn == 1 (последний), теперь берём rn <= limit_per_coin —
        то есть последние N штук, чтобы у ИИ была история, а не одна точка.

        Результат отсортирован по coin_id и по возрастанию даты внутри монеты —
        удобно сразу группировать и отдавать как временной ряд.
        """
        if not coin_list:
            return []

        ranked_subq = (
            select(
                MarketSnapshotModel,
                func.row_number()
                .over(
                    partition_by=MarketSnapshotModel.coin_id,
                    order_by=MarketSnapshotModel.created_at.desc(),
                )
                .label("rn"),
            )
            .where(MarketSnapshotModel.coin_id.in_(coin_list))
            .subquery()
        )

        latest_snapshot = aliased(MarketSnapshotModel, ranked_subq)

        stmt = (
            select(latest_snapshot)
            .where(ranked_subq.c.rn <= limit_per_coin)
            .order_by(latest_snapshot.coin_id, latest_snapshot.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())