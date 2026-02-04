from aiogram import Bot

from app import db


class ChannelLinkService:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def add_channel(self, chat_id: int, invite_link: str):
        # Validate access using chat_id (invite links may not resolve via API)
        await self.bot.get_chat(chat_id)
        created = db.add_channel(invite_link=invite_link, chat_id=chat_id)
        if not created:
            raise ValueError("Channel already exists.")
        return invite_link, chat_id

    @staticmethod
    async def refresh_invite(invite_link: str):
        channel = db.get_channel(invite_link)
        if not channel:
            raise ValueError("Channel not found.")
        return channel.invite_link

    @staticmethod
    async def remove_channel(invite_link: str):
        channel = db.get_channel(invite_link)
        if not channel:
            raise ValueError("Channel not found.")
        removed = db.remove_channel(invite_link)
        if not removed:
            raise ValueError("Failed to remove channel.")
        return True

    @staticmethod
    def list_channels():
        return db.list_channels()
