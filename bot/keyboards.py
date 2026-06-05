from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_poll_keyboard(poll_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да", callback_data=f"vote:{poll_id}:yes")
    builder.button(text="❌ Нет", callback_data=f"vote:{poll_id}:no")
    builder.adjust(2)
    return builder.as_markup()


def get_poll_keyboard_with_votes(poll_id: int, yes_count: int, no_count: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"✅ Да ({yes_count})", callback_data=f"vote:{poll_id}:yes")
    builder.button(text=f"❌ Нет ({no_count})", callback_data=f"vote:{poll_id}:no")
    builder.adjust(2)
    return builder.as_markup()