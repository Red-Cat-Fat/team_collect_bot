from datetime import datetime
from typing import Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.database.models import Base, Poll, Vote, GameSchedule


class Database:
    def __init__(self, db_path: str):
        self.engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def init(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self):
        await self.engine.dispose()

    async def get_session(self) -> AsyncSession:
        return self.session_factory()

    async def create_poll(self, question: str, message_id: int, thread_id: int) -> Poll:
        async with self.session_factory() as session:
            poll = Poll(question=question, message_id=message_id, thread_id=thread_id)
            session.add(poll)
            await session.commit()
            await session.refresh(poll)
            return poll

    async def get_active_poll(self) -> Optional[Poll]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Poll).where(Poll.is_active == True).order_by(Poll.created_at.desc())
            )
            return result.scalar_one_or_none()

    async def get_poll_by_id(self, poll_id: int) -> Optional[Poll]:
        async with self.session_factory() as session:
            result = await session.execute(select(Poll).where(Poll.id == poll_id))
            return result.scalar_one_or_none()

    async def deactivate_poll(self, poll_id: int):
        async with self.session_factory() as session:
            await session.execute(update(Poll).where(Poll.id == poll_id).values(is_active=False))
            await session.commit()

    async def create_vote(self, poll_id: int, user_id: int, username: Optional[str], answer: bool) -> Vote:
        async with self.session_factory() as session:
            vote = Vote(poll_id=poll_id, user_id=user_id, username=username, answer=answer)
            session.add(vote)
            await session.commit()
            await session.refresh(vote)
            return vote

    async def update_vote(self, poll_id: int, user_id: int, answer: bool):
        async with self.session_factory() as session:
            await session.execute(
                update(Vote)
                .where(Vote.poll_id == poll_id, Vote.user_id == user_id)
                .values(answer=answer, voted_at=datetime.utcnow())
            )
            await session.commit()

    async def get_vote(self, poll_id: int, user_id: int) -> Optional[Vote]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Vote).where(Vote.poll_id == poll_id, Vote.user_id == user_id)
            )
            return result.scalar_one_or_none()

    async def get_votes(self, poll_id: int) -> list[Vote]:
        async with self.session_factory() as session:
            result = await session.execute(select(Vote).where(Vote.poll_id == poll_id).order_by(Vote.voted_at))
            return list(result.scalars().all())

    async def get_yes_votes(self, poll_id: int) -> list[Vote]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Vote).where(Vote.poll_id == poll_id, Vote.answer == True).order_by(Vote.voted_at)
            )
            return list(result.scalars().all())

    async def create_game_schedule(self, game_date: datetime) -> GameSchedule:
        async with self.session_factory() as session:
            schedule = GameSchedule(game_date=game_date)
            session.add(schedule)
            await session.commit()
            await session.refresh(schedule)
            return schedule

    async def get_latest_schedule(self) -> Optional[GameSchedule]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(GameSchedule).order_by(GameSchedule.created_at.desc())
            )
            return result.scalar_one_or_none()

    async def get_pending_schedule(self) -> Optional[GameSchedule]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(GameSchedule).where(GameSchedule.reminder_sent == False).order_by(GameSchedule.game_date)
            )
            return result.scalar_one_or_none()

    async def link_poll_to_schedule(self, schedule_id: int, poll_id: int):
        async with self.session_factory() as session:
            await session.execute(update(GameSchedule).where(GameSchedule.id == schedule_id).values(poll_id=poll_id))
            await session.commit()

    async def mark_reminder_sent(self, schedule_id: int):
        async with self.session_factory() as session:
            await session.execute(update(GameSchedule).where(GameSchedule.id == schedule_id).values(reminder_sent=True))
            await session.commit()

    async def get_poll_with_votes(self, poll_id: int):
        async with self.session_factory() as session:
            result = await session.execute(select(Poll).where(Poll.id == poll_id))
            poll = result.scalar_one_or_none()
            if poll:
                votes_result = await session.execute(select(Vote).where(Vote.poll_id == poll_id))
                poll.votes = list(votes_result.scalars().all())
            return poll