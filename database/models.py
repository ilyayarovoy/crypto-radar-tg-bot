from sqlalchemy import String, ForeignKey, Text, BigInteger, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func
from datetime import datetime

from database.base import Base

class UserModel(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    first_name: Mapped[str | None] = mapped_column(nullable=True, default=None)
    last_name: Mapped[str | None] = mapped_column(nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)


class UserFavoriteCoinsModel(Base): #Избранные монеты
    __tablename__ = 'user_favorite_coins'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    coin_id: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)


class MarketSnapshotModel(Base):
  __tablename__ = 'market_snapshots'

  id: Mapped[int] = mapped_column(primary_key=True)
  coin_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)

  name: Mapped[str] = mapped_column(String(100), nullable=False)
  image: Mapped[str | None] = mapped_column(String(255), nullable=True)
  current_price: Mapped[float] = mapped_column(Float, nullable=False)
  market_cap: Mapped[float | None] = mapped_column(Float, nullable=True)
  fully_diluted_valuation: Mapped[float | None] = mapped_column(Float, nullable=True)
  total_volume: Mapped[float | None] = mapped_column(Float, nullable=True)
  high_24h: Mapped[float | None] = mapped_column(Float, nullable=True)
  low_24h: Mapped[float | None] = mapped_column(Float, nullable=True)
  price_change_24h: Mapped[float | None] = mapped_column(Float, nullable=True)
  price_change_percentage_24h: Mapped[float | None] = mapped_column(Float, nullable=True)
  market_cap_change_24h: Mapped[float | None] = mapped_column(Float, nullable=True)
  market_cap_change_percentage_24h: Mapped[float | None] = mapped_column(Float, nullable=True)
  circulating_supply: Mapped[float | None] = mapped_column(Float, nullable=True)
  total_supply: Mapped[float | None] = mapped_column(Float, nullable=True)
  ath: Mapped[float | None] = mapped_column(Float, nullable=True)

  # Время создания записи (критично для выборки истории для ИИ)
  created_at: Mapped[datetime] = mapped_column(
      DateTime, server_default=func.now(), index=True, nullable=False
  )


class PriceAlertModel(Base):
    __tablename__ = 'price_alerts'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    coin_id: Mapped[str] = mapped_column(String(50), nullable=False)
    condition: Mapped[str] = mapped_column(String(2), nullable=False)  # >, <, >=, <=
    target_price: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)


