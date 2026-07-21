import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    games_played: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    games_won: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Зв'язки (Relationships)
    game_history: Mapped[List["GamePlayer"]] = relationship(back_populates="user")
    won_games: Mapped[List["Game"]] = relationship(back_populates="winner")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # "CHOICE" або "NUMBER"
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # JSONB для варіантів відповідей, наприклад: {"A": "Київ", "B": "Львів", ...}
    options: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    correct_answer: Mapped[str] = mapped_column(String(255), nullable=False)


class Game(Base):
    __tablename__ = "games"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    winner_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Зв'язки
    winner: Mapped[Optional["User"]] = relationship(back_populates="won_games")
    players: Mapped[List["GamePlayer"]] = relationship(back_populates="game")


class GamePlayer(Base):
    """ Проміжна таблиця (Many-to-Many з додатковими даними) для результатів матчу """
    __tablename__ = "game_players"

    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    final_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    placement: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1, 2 або 3 місце

    # Зв'язки
    game: Mapped["Game"] = relationship(back_populates="players")
    user: Mapped["User"] = relationship(back_populates="game_history")