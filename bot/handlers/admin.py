from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.types import Message, ChatMember
from aiogram.filters import Command, CommandObject
from aiogram.enums import ParseMode

from bot.config import config
from bot.database import Database
from bot.keyboards import get_poll_keyboard, get_poll_keyboard_with_votes
from bot.utils.mentions import format_mentions

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in config.admin_ids


@router.message(Command("set_game_date"))
async def cmd_set_game_date(message: Message, command: CommandObject, db: Database, bot: Bot):
    if not is_admin(message.from_user.id):
        await message.reply("⛔ У вас нет прав для этой команды.")
        return

    if not command.args:
        await message.reply("Использование: <code>/set_game_date DD-MM</code>\nПример: <code>/set_game_date 15-06</code>", parse_mode=ParseMode.HTML)
        return

    try:
        day, month = map(int, command.args.split("-"))
        now = datetime.now()
        game_date = datetime(now.year, month, day)
        if game_date < now:
            game_date = datetime(now.year + 1, month, day)
    except ValueError:
        await message.reply("Неверный формат даты. Используйте <code>DD-MM</code>.", parse_mode=ParseMode.HTML)
        return

    schedule = await db.create_game_schedule(game_date)
    await message.reply(
        f"✅ Дата игры установлена: <b>{game_date.strftime('%d.%m.%Y')}</b>\n"
        f"Ежедневный опрос начнётся с завтрашнего дня в 10:00.",
        parse_mode=ParseMode.HTML
    )


@router.message(Command("who_is_going"))
async def cmd_who_is_going(message: Message, db: Database):
    if not is_admin(message.from_user.id):
        await message.reply("⛔ У вас нет прав для этой команды.")
        return

    schedule = await db.get_latest_schedule()
    if not schedule or not schedule.poll_id:
        await message.reply("Нет активного опроса.")
        return

    votes = await db.get_yes_votes(schedule.poll_id)
    if not votes:
        await message.reply("Пока никто не проголосовал «Да».")
        return

    users = [(v.user_id, v.username) for v in votes]
    text = f"📋 <b>Едут на игру ({schedule.game_date:%d.%m.%Y}):</b>\n\n{format_mentions(users)}"
    await message.reply(text, parse_mode=ParseMode.HTML)


async def get_chat_members(bot: Bot) -> list[tuple[int, str | None]]:
    members = []
    try:
        async for member in bot.get_chat_members(config.topic_id):
            if not member.user.is_bot:
                members.append((member.user.id, member.user.username))
    except Exception:
        pass
    return members


async def build_poll_text(poll_question: str, yes_votes: list, no_votes: list, all_members: list, voted_user_ids: set) -> str:
    yes_users = [(v.user_id, v.username) for v in yes_votes]
    no_users = [(v.user_id, v.username) for v in no_votes]

    not_voted = [(uid, uname) for uid, uname in all_members if uid not in voted_user_ids]

    lines = [
        poll_question,
        "",
        f"✅ <b>Едут ({len(yes_votes)}):</b> {format_mentions(yes_users) if yes_users else 'никто'}",
        f"❌ <b>Не едут ({len(no_votes)}):</b> {format_mentions(no_users) if no_users else 'никто'}",
    ]

    if not_voted:
        lines.append("")
        lines.append(f"⏳ <b>Не ответили ({len(not_voted)}):</b> {format_mentions(not_voted)}")

    return "\n".join(lines)


async def send_or_update_poll(bot: Bot, db: Database, schedule_id: int, game_date: datetime):
    schedule = await db.get_latest_schedule()
    if not schedule or schedule.id != schedule_id:
        return

    poll_question = f"Ты поедешь на игру в {game_date.strftime('%A, %d.%m.%Y')}?"
    all_members = await get_chat_members(bot)

    if schedule.poll_id:
        poll = await db.get_poll_with_votes(schedule.poll_id)
        if poll:
            yes_votes = [v for v in poll.votes if v.answer]
            no_votes = [v for v in poll.votes if not v.answer]
            voted_user_ids = {v.user_id for v in poll.votes}

            text = await build_poll_text(poll_question, yes_votes, no_votes, all_members, voted_user_ids)

            try:
                await bot.edit_message_text(
                    text=text,
                    chat_id=config.topic_id,
                    message_id=poll.message_id,
                    reply_markup=get_poll_keyboard_with_votes(poll.id, len(yes_votes), len(no_votes)),
                    parse_mode=ParseMode.HTML
                )
                return
            except Exception:
                pass

    sent = await bot.send_message(
        chat_id=config.topic_id,
        text=poll_question,
        message_thread_id=config.topic_id,
        reply_markup=get_poll_keyboard(0),
        parse_mode=ParseMode.HTML
    )

    poll = await db.create_poll(poll_question, sent.message_id, sent.message_thread_id or sent.chat.id)
    await db.link_poll_to_schedule(schedule_id, poll.id)

    await bot.edit_message_reply_markup(
        chat_id=sent.chat.id,
        message_id=sent.message_id,
        reply_markup=get_poll_keyboard(poll.id)
    )