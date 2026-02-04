import logging

from aiogram import Bot
from aiogram.enums import ChatMemberStatus

from app import db
from app.config import ADMIN_IDS


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def is_member(bot: Bot, user_id: int) -> bool:
    channels = db.list_channels()
    if not channels:
        return True
    allowed_statuses = {
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.CREATOR,
        ChatMemberStatus.RESTRICTED,
    }
    for channel in channels:
        try:
            member = await bot.get_chat_member(chat_id=channel.chat_id, user_id=user_id)
        except Exception as e:
            logging.error(e)
            if db.has_pending_join_request(user_id, channel.chat_id):
                continue
            return False
        if member.status in allowed_statuses:
            continue
        if db.has_pending_join_request(user_id, channel.chat_id):
            continue
        return False
    return True


def escape_md(text: str) -> str:
    for ch in "_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text


def format_caption(name: str, description: str, code: str | None = None) -> str:
    safe_name = escape_md(name)
    safe_desc = escape_md(description)
    caption = f"*{safe_name}*\n{safe_desc}"
    if code:
        caption += f"\n`{escape_md(code)}`"
    return caption