from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import CHANNELS


def delete_button_keyboard(code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Delete", callback_data=f"delreq:{code}")]]
    )


def confirm_delete_keyboard(code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Confirm delete", callback_data=f"delok:{code}"),
                InlineKeyboardButton(text="Cancel", callback_data=f"delcancel:{code}"),
            ]
        ]
    )


async def build_join_keyboard(bot: Bot) -> InlineKeyboardMarkup:
    rows = []
    for channel_id in CHANNELS:
        url = None
        try:
            chat = await bot.get_chat(channel_id)
            if getattr(chat, "username", None):
                url = f"https://t.me/{chat.username}"
        except Exception:  # noqa
            pass
        if url is None:
            fallback = str(channel_id).removeprefix("-100")
            url = f"https://t.me/c/{fallback}"
        rows.append([InlineKeyboardButton(text="Join", url=url)])
    rows.append([InlineKeyboardButton(text="I've joined ✅", callback_data="recheck_membership")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
