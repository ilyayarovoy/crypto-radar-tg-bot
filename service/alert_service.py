import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import PriceAlertModel
from service.user_service import UserService

logger = logging.getLogger(__name__)


class AlertService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_alert(
        self,
        tg_id: int,
        coin_id: str,
        condition: str,
        target_price: float
    ) -> PriceAlertModel | None:
        """Создать новый ценовой алерт для пользователя"""
        user_service = UserService(self.session)
        user = await user_service.get_user_by_tg_id(tg_id=tg_id)

        if not user:
            logger.warning(f"Попытка создать алерт для несуществующего пользователя tg_id={tg_id}")
            return None

        alert = PriceAlertModel(
            user_id=user.id,
            coin_id=coin_id.lower(),
            condition=condition,
            target_price=target_price,
            is_active=True
        )

        self.session.add(alert)
        await self.session.commit()
        await self.session.refresh(alert)

        logger.info(f"Создан алерт #{alert.id} для user {tg_id}: {coin_id} {condition} {target_price}")
        return alert

    async def get_user_active_alerts(self, tg_id: int) -> list[PriceAlertModel]:
        """Получить все активные алерты пользователя"""
        user_service = UserService(self.session)
        user = await user_service.get_user_by_tg_id(tg_id=tg_id)

        if not user:
            return []

        stmt = select(PriceAlertModel).where(
            PriceAlertModel.user_id == user.id,
            PriceAlertModel.is_active == True
        ).order_by(PriceAlertModel.created_at.desc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_active_alerts(self) -> list[PriceAlertModel]:
        """Получить все активные алерты всех пользователей (для фоновой проверки)"""
        stmt = select(PriceAlertModel).where(
            PriceAlertModel.is_active == True
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def deactivate_alert(self, alert_id: int) -> bool:
        """Деактивировать алерт после срабатывания"""
        stmt = select(PriceAlertModel).where(PriceAlertModel.id == alert_id)
        result = await self.session.execute(stmt)
        alert = result.scalar_one_or_none()

        if not alert:
            return False

        alert.is_active = False
        from datetime import datetime
        alert.triggered_at = datetime.now()
        await self.session.commit()

        logger.info(f"Алерт #{alert_id} деактивирован")
        return True

    async def delete_alert(self, alert_id: int, tg_id: int) -> bool:
        """Удалить алерт (только если он принадлежит пользователю)"""
        user_service = UserService(self.session)
        user = await user_service.get_user_by_tg_id(tg_id=tg_id)

        if not user:
            return False

        stmt = select(PriceAlertModel).where(
            PriceAlertModel.id == alert_id,
            PriceAlertModel.user_id == user.id
        )
        result = await self.session.execute(stmt)
        alert = result.scalar_one_or_none()

        if not alert:
            return False

        await self.session.delete(alert)
        await self.session.commit()

        logger.info(f"Алерт #{alert_id} удален пользователем {tg_id}")
        return True

    async def get_unique_coin_ids(self) -> list[str]:
        """Получить список уникальных coin_id из активных алертов (для оптимизации запросов к API)"""
        stmt = select(PriceAlertModel.coin_id).where(
            PriceAlertModel.is_active == True
        ).distinct()
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
