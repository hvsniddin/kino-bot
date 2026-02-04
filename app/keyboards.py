from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app import db


def delete_button_keyboard(code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="O'chirish", callback_data=f"delreq:{code}")]]
    )


def confirm_delete_keyboard(code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Tasdiqlash", callback_data=f"delok:{code}"),
                InlineKeyboardButton(text="Bekor qilish", callback_data=f"delcancel:{code}"),
            ]
        ]
    )


def confirm_channel_delete_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Tasdiqlash", callback_data=f"chdelokid:{chat_id}"),
                InlineKeyboardButton(text="Bekor qilish", callback_data=f"chdelcancelid:{chat_id}"),
            ]
        ]
    )


def build_join_keyboard() -> InlineKeyboardMarkup:
    rows = []
    channels = db.list_channels()
    for idx, channel in enumerate(channels, start=1):
        label = f"Channel {idx}"
        rows.append([InlineKeyboardButton(text=label, url=channel.invite_link)])
    rows.append([InlineKeyboardButton(text="✅ Confirm", callback_data="recheck_membership")])
    return InlineKeyboardMarkup(inline_keyboard=rows)