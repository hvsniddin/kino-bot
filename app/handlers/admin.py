from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.config import STORAGE_CHANNEL_ID
from app.db import get_movie_record, remove_movie, save_movie
from app.keyboards import confirm_delete_keyboard, delete_button_keyboard
from app.states import AddMovie
from app.utils import format_caption, is_admin

router = Router()


@router.message(Command("add"))
async def add_movie(message: types.Message, state: FSMContext):
    if message.from_user is None or not is_admin(message.from_user.id):
        await message.answer("You are not authorized to add movies.")
        return
    if STORAGE_CHANNEL_ID is None:
        await message.answer("Storage channel is not configured.")
        return
    await state.set_state(AddMovie.waiting_for_video)
    await message.answer("Send the movie video to store.")


@router.message(AddMovie.waiting_for_video, F.video)
async def receive_movie_video(message: types.Message, state: FSMContext):
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(AddMovie.waiting_for_name)
    await message.answer("Video received. Send the movie name.")


@router.message(AddMovie.waiting_for_video)
async def expect_video(message: types.Message):
    await message.answer("Please send a video file to proceed.")


@router.message(AddMovie.waiting_for_name, F.text)
async def receive_movie_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("Name cannot be empty. Send a valid name.")
        return
    await state.update_data(name=name)
    await state.set_state(AddMovie.waiting_for_description)
    await message.answer("Send the movie description.")


@router.message(AddMovie.waiting_for_name)
async def expect_name(message: types.Message):
    await message.answer("Send the movie name as text.")


@router.message(AddMovie.waiting_for_description, F.text)
async def receive_movie_description(message: types.Message, state: FSMContext):
    description = message.text.strip()
    if not description:
        await message.answer("Description cannot be empty. Send a valid description.")
        return
    await state.update_data(description=description)
    await state.set_state(AddMovie.waiting_for_code)
    await message.answer("Send the movie code.")


@router.message(AddMovie.waiting_for_description)
async def expect_description(message: types.Message):
    await message.answer("Send the movie description as text.")


@router.message(AddMovie.waiting_for_code, F.text)
async def receive_movie_code(message: types.Message, state: FSMContext):
    data = await state.get_data()
    file_id = data.get("file_id")
    name = data.get("name", "")
    description = data.get("description", "")
    code = message.text.strip()
    if not file_id:
        await message.answer("No video stored in state. Restart with /add.")
        await state.clear()
        return
    if not code:
        await message.answer("Code cannot be empty. Send a valid code.")
        return
    caption = format_caption(name, description, code)
    keyboard = delete_button_keyboard(code)
    sent = await message.bot.send_video(
        chat_id=STORAGE_CHANNEL_ID,
        video=file_id,
        caption=caption,
        reply_markup=keyboard,
    )
    if save_movie(code, file_id, sent.message_id, name, description):
        await message.answer(f"Movie registered with code: {code}")
    else:
        await message.answer("This movie code already exists. Use another code.")
    await state.clear()


@router.message(AddMovie.waiting_for_code)
async def expect_code(message: types.Message):
    await message.answer("Send the movie code as text.")


@router.message(Command("remove"))
async def remove_movie_command(message: types.Message):
    if message.from_user is None or not is_admin(message.from_user.id):
        await message.answer("You are not authorized to remove movies.")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("Usage: /remove <code>")
        return
    code = parts[1].strip()
    record = get_movie_record(code)
    if not record:
        await message.answer("Movie code not found.")
        return
    await message.answer(
        f"Confirm delete for `{code}`?",
        reply_markup=confirm_delete_keyboard(code),
    )


@router.callback_query(F.data.startswith("delreq:"))
async def delete_request(callback: types.CallbackQuery):
    code = callback.data.split(":", 1)[1]
    if callback.from_user is None or not is_admin(callback.from_user.id):
        await callback.answer("Not authorized", show_alert=True)
        return
    await callback.answer()
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=confirm_delete_keyboard(code))
        except Exception:  # noqa
            pass


@router.callback_query(F.data.startswith("delcancel:"))
async def delete_cancel(callback: types.CallbackQuery):
    code = callback.data.split(":", 1)[1]
    if callback.from_user is None or not is_admin(callback.from_user.id):
        await callback.answer("Not authorized", show_alert=True)
        return
    await callback.answer("Cancelled")
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=delete_button_keyboard(code))
        except Exception:  # noqa
            pass


@router.callback_query(F.data.startswith("delok:"))
async def delete_confirm(callback: types.CallbackQuery):
    code = callback.data.split(":", 1)[1]
    if callback.from_user is None or not is_admin(callback.from_user.id):
        await callback.answer("Not authorized", show_alert=True)
        return
    record = get_movie_record(code)
    if not record:
        await callback.answer("Movie not found", show_alert=True)
        try:
            if callback.message:
                await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:  # noqa
            pass
        return
    _, _, storage_message_id, _, _ = record
    removed = remove_movie(code)
    if STORAGE_CHANNEL_ID and storage_message_id:
        try:
            await callback.bot.delete_message(chat_id=STORAGE_CHANNEL_ID, message_id=storage_message_id)
        except Exception:  # noqa
            pass
    await callback.answer("Movie removed" if removed else "Failed to remove", show_alert=True)
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:  # noqa
            pass
