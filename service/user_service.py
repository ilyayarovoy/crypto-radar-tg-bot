from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import UserModel

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session


    async def get_all_users(self):
        stmt = select(UserModel)
        result = await self.session.execute(stmt)
        return result.scalars().all()


    async def get_user_by_tg_id(self, tg_id: int):
        stmt = select(UserModel).where(UserModel.tg_id == tg_id)
        user = await self.session.execute(stmt)
        return user.scalar_one_or_none()

    async def create_user(self,
                          tg_id: int,
                          username: str,
                          first_name: str,
                          last_name: str):

        new_user = UserModel(
            tg_id=tg_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )

        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        return new_user