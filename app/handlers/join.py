from aiogram import Router
from aiogram.enums import ChatMemberStatus
from aiogram.types import ChatJoinRequest, ChatMemberUpdated

from app import db

router = Router()


@router.chat_join_request()
async def handle_join_request(event: ChatJoinRequest):
    # Store pending join request so users can be treated as eligible while awaiting approval
    db.upsert_join_request(user_id=event.from_user.id, chat_id=event.chat.id, status="pending")


@router.chat_member()
async def handle_chat_member(update: ChatMemberUpdated):
    new_status = update.new_chat_member.status
    user_id = update.new_chat_member.user.id
    chat_id = update.chat.id
    if new_status in {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR}:
        # Remove pending request once user is admitted
        db.remove_join_request(user_id=user_id, chat_id=chat_id)
    elif new_status in {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED}:
        # Cleanup any lingering requests if user leaves/removed
        db.remove_join_request(user_id=user_id, chat_id=chat_id)
