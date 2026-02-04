from aiogram import F, Router, types
from aiogram.filters import Command

from app.db import get_movie_record
from app.keyboards import build_join_keyboard
from app.utils import format_caption, is_member

router = Router()


@router.message(Command("start"))
async def start_command(message: types.Message):
    if message.from_user is None:
        return
    if not await is_member(message.bot, message.from_user.id):
        keyboard = build_join_keyboard()
        await message.answer("You must join the required channels to use this bot.", reply_markup=keyboard)
        return
    await message.answer("Welcome! Send the movie code to receive the file.")


@router.message(F.text)
async def handle_movie_request(message: types.Message):
    if message.from_user is None:
        return
    if not await is_member(message.bot, message.from_user.id):
        keyboard = build_join_keyboard()
        await message.answer("You must join the required channels to use this bot.", reply_markup=keyboard)
        return
    code = message.text.strip()
    record = get_movie_record(code)
    if not record:
        await message.answer("Invalid or unknown movie code.")
        return
    _, file_id, _, name, description = record
    caption = format_caption(name or "", description or "")
    await message.bot.send_video(chat_id=message.chat.id, video=file_id, caption=caption)


@router.message()
async def unsupported_message(message: types.Message):
    await message.answer("Send a movie code as text.")


@router.callback_query(F.data == "recheck_membership")
async def recheck_membership(callback: types.CallbackQuery):
    if callback.from_user is None:
        await callback.answer()
        return
    await callback.answer()
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id if callback.message else callback.from_user.id
    if not await is_member(callback.bot, user_id):
        keyboard = build_join_keyboard()
        await callback.bot.send_message(
            chat_id,
            "You must join the required channels to use this bot.",
            reply_markup=keyboard,
        )
    else:
        await callback.bot.send_message(chat_id, "Welcome! Send the movie code to receive the file.")

