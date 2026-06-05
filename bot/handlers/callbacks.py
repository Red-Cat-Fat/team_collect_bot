from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode

from bot.config import config
from bot.database import Database
from bot.keyboards import get_poll_keyboard_with_votes
from bot.utils.mentions import format_mentions

router = Router()


async def get_chat_members(bot: Bot) -> list[tuple[int, str | None]]:
    members = []
    try:
        async for member in bot.get_chat_members(config.topic_id):
            if not member.user.is_bot:
                members.append((member.user.id, member.user.username))
    except Exception:
        pass
    return members


@router.callback_query(F.data.startswith("vote:"))
async def handle_vote(callback: CallbackQuery, db: Database, bot: Bot):
    try:
        _, poll_id_str, answer_str = callback.data.split(":")
        poll_id = int(poll_id_str)
        answer = answer_str == "yes"
    except (ValueError, IndexError):
        await callback.answer("Ошибка обработки голоса", show_alert=True)
        return

    poll = await db.get_poll_by_id(poll_id)
    if not poll or not poll.is_active:
        await callback.answer("Опрос уже завершен", show_alert=True)
        return

    if callback.message.message_thread_id != poll.thread_id:
        await callback.answer("Голосовать можно только в топике опроса", show_alert=True)
        return

    existing_vote = await db.get_vote(poll_id, callback.from_user.id)

    if existing_vote:
        if existing_vote.answer == answer:
            await callback.answer("Вы уже так проголосовали", show_alert=False)
            return
        await db.update_vote(poll_id, callback.from_user.id, answer)
        await callback.answer("Голос изменен!")
    else:
        await db.create_vote(poll_id, callback.from_user.id, callback.from_user.username, answer)
        await callback.answer("Голос засчитан!")

    votes = await db.get_votes(poll_id)
    yes_votes = [v for v in votes if v.answer]
    no_votes = [v for v in votes if not v.answer]

    all_members = await get_chat_members(bot)
    voted_user_ids = {v.user_id for v in votes}
    not_voted = [(uid, uname) for uid, uname in all_members if uid not in voted_user_ids]

    yes_users = [(v.user_id, v.username) for v in yes_votes]
    no_users = [(v.user_id, v.username) for v in no_votes]

    lines = [
        poll.question,
        "",
        f"✅ <b>Едут ({len(yes_votes)}):</b> {format_mentions(yes_users) if yes_users else 'никто'}",
        f"❌ <b>Не едут ({len(no_votes)}):</b> {format_mentions(no_users) if no_users else 'никто'}",
    ]

    if not_voted:
        lines.append("")
        lines.append(f"⏳ <b>Не ответили ({len(not_voted)}):</b> {format_mentions(not_voted)}")

    text = "\n".join(lines)

    try:
        await bot.edit_message_text(
            text=text,
            chat_id=callback.message.chat.id,
            message_id=poll.message_id,
            reply_markup=get_poll_keyboard_with_votes(poll_id, len(yes_votes), len(no_votes)),
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass