from aiogram import Bot
from aiogram.enums import ChatMemberStatus

from app.config import ADMIN_IDS, CHANNELS


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def is_member(bot: Bot, user_id: int) -> bool:
    if not CHANNELS:
        return True
    for channel_id in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        except Exception:  # noqa
            return False
        if member.status not in {
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
        }:
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
