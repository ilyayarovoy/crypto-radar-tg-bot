import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import UserFavoriteCoinsModel
from service.user_service import UserService

logger = logging.getLogger(__name__)


class UserFavoriteCoinsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_favorite_coins_by_user(self, tg_id: int) -> list[str]:
        user_service = UserService(self.session)
        user = await user_service.get_user_by_tg_id(tg_id=tg_id)
        if not user:
            return []

        stmt = select(UserFavoriteCoinsModel.coin_id).where(
            UserFavoriteCoinsModel.user_id == user.id
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_favorite_coin(self, tg_id: int, coin: str) -> None:
        user_service = UserService(self.session)
        user = await user_service.get_user_by_tg_id(tg_id=tg_id)
        if not user:
            logger.warning("Попытка добавить монету несуществующему пользователю tg_id=%s", tg_id)
            return

        # Проверяем, что монета ещё не добавлена, чтобы не плодить дубликаты
        stmt = select(UserFavoriteCoinsModel).where(
            UserFavoriteCoinsModel.user_id == user.id,
            UserFavoriteCoinsModel.coin_id == coin,
        )
        existing = await self.session.execute(stmt)
        if existing.scalar_one_or_none():
            return

        self.session.add(UserFavoriteCoinsModel(user_id=user.id, coin_id=coin))
        await self.session.commit()

    async def remove_favorite_coin(self, tg_id: int, coin: str) -> None:
        user_service = UserService(self.session)
        user = await user_service.get_user_by_tg_id(tg_id=tg_id)
        if not user:
            return

        stmt = select(UserFavoriteCoinsModel).where(
            UserFavoriteCoinsModel.user_id == user.id,
            UserFavoriteCoinsModel.coin_id == coin,
        )
        result = await self.session.execute(stmt)
        obj = result.scalar_one_or_none()
        if obj:
            await self.session.delete(obj)
            await self.session.commit()

    async def get_all_distinct_favorite_coins(self) -> list[str]:

        stmt = select(UserFavoriteCoinsModel.coin_id).distinct()
        result = await self.session.execute(stmt)
        return list(result.scalars().all())