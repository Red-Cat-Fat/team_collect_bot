from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Poll(Base):
    __tablename__ = "polls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(String(512), nullable=False)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    thread_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    votes: Mapped[list["Vote"]] = relationship(back_populates="poll", cascade="all, delete-orphan")
    game_schedule: Mapped["GameSchedule"] = relationship(back_populates="poll", uselist=False)


class Vote(Base):
    __tablename__ = "votes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    poll_id: Mapped[int] = mapped_column(Integer, ForeignKey("polls.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    username: Mapped[str | None] = mapped_column(String(256), nullable=True)
    answer: Mapped[bool] = mapped_column(Boolean, nullable=False)
    voted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    poll: Mapped["Poll"] = relationship(back_populates="votes")

    __table_args__ = (UniqueConstraint("poll_id", "user_id", name="uq_poll_user"),)


class GameSchedule(Base):
    __tablename__ = "game_schedule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    poll_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("polls.id", ondelete="SET NULL"), nullable=True)
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    poll: Mapped["Poll"] = relationship(back_populates="game_schedule")