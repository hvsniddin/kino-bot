import logging
from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from app.config import STORAGE_CHANNEL_ID
from app.db import (
    get_movie_record,
    remove_movie,
    save_movie,
    list_channels,
    get_channel_by_chat_id,
)
from app.keyboards import (
    confirm_channel_delete_keyboard,
    confirm_delete_keyboard,
    delete_button_keyboard,
)
from app.services.channel_links import ChannelLinkService
from app.states import AddMovie
from app.utils import escape_md, format_caption, is_admin

router = Router()


@router.message(Command("add"))
async def add_movie(message: types.Message, state: FSMContext):
    if message.from_user is None or not is_admin(message.from_user.id):
        return
    if STORAGE_CHANNEL_ID is None:
        await message.answer("Storage channel is not configured.")
        return
    await state.set_state(AddMovie.waiting_for_video)
    await message.answer("Kinoni yuboring.")


@router.message(AddMovie.waiting_for_video, F.video)
async def receive_movie_video(message: types.Message, state: FSMContext):
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(AddMovie.waiting_for_name)
    await message.answer("Kino qabul qilindi. Kino nomini kiriting.")


@router.message(AddMovie.waiting_for_video)
async def expect_video(message: types.Message):
    await message.answer("Iltimos, kinoni video shaklida yuboring.")


@router.message(AddMovie.waiting_for_name, F.text)
async def receive_movie_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("Iltimos, kino nomini text shaklida yuboring.")
        return
    await state.update_data(name=name)
    await state.set_state(AddMovie.waiting_for_description)
    await message.answer("Kino tavsifini yuboring.")


@router.message(AddMovie.waiting_for_name)
async def expect_name(message: types.Message):
    await message.answer("Iltimos, kino nomini text shaklida yuboring.")


@router.message(AddMovie.waiting_for_description, F.text)
async def receive_movie_description(message: types.Message, state: FSMContext):
    description = message.text.strip()
    if not description:
        await message.answer("Iltimos, kino tavsifini text shaklida yuboring.")
        return
    await state.update_data(description=description)
    await state.set_state(AddMovie.waiting_for_code)
    await message.answer("Kino kodini yuboring.")


@router.message(AddMovie.waiting_for_description)
async def expect_description(message: types.Message):
    await message.answer("Iltimos, kino tavsifini text shaklida yuboring..")


@router.message(AddMovie.waiting_for_code, F.text)
async def receive_movie_code(message: types.Message, state: FSMContext):
    data = await state.get_data()
    file_id = data.get("file_id")
    name = data.get("name", "")
    description = data.get("description", "")
    code = message.text.strip()
    if not file_id:
        await message.answer("❌ Xatolik yuz berdi. Qayta urinib ko'ring /add.")
        await state.clear()
        return
    if not code:
        await message.answer("Iltimos, kino kodini text shaklida yuboring.")
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
        await message.answer(f"✅ Kino `{name}` muvaffaqiyatli qo'shildi.")
    else:
        await message.answer("Bu kod allaqachon ishlatilga. Boshqa kod bilan urinib ko'ring.")
    await state.clear()


@router.message(AddMovie.waiting_for_code)
async def expect_code(message: types.Message):
    await message.answer("Iltimos, kino kodini text shaklida yuboring.")


@router.message(Command("remove"))
async def remove_movie_command(message: types.Message):
    if message.from_user is None or not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("Ishlatish: /remove <code>")
        return
    code = parts[1].strip()
    record = get_movie_record(code)
    if not record:
        await message.answer("Kino topilmadi.")
        return
    await message.answer(
        f"Ushbi kodli kinoni o'chirishni xohlaysizmi: `{code}`?",
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
    await callback.answer("Bekor qilindi")
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
        await callback.answer("Kino topilmadi", show_alert=True)
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
    await callback.answer("✅ Kino o'chirildi" if removed else "❌ Xatolik yuz berdi", show_alert=True)
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:  # noqa
            pass


@router.message(Command("addchannel"))
async def add_channel_command(message: types.Message):
    if message.from_user is None or not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Usage: /addchannel <chat\\_id> <invite\\_link>")
        return
    try:
        chat_id = int(parts[1].strip())
    except ValueError:
        await message.answer("chat_id must be an integer")
        return
    invite_link = parts[2].strip()
    service = ChannelLinkService(message.bot)
    try:
        invite_link, _chat_id = await service.add_channel(chat_id=chat_id, invite_link=invite_link)
    except ValueError as exc:
        await message.answer(str(exc))
        return
    except Exception as e:
        logging.error(e)
        await message.answer("Failed to add channel. Make sure the bot is admin and IDs/links are valid.")
        return
    await message.answer(
        f"✅ Channel added\\.\nID: `{chat_id}`\nInvite: {escape_md(invite_link)}",
        parse_mode="MarkdownV2",
    )


@router.message(Command("channels"))
async def list_channels_command(message: types.Message):
    if message.from_user is None or not is_admin(message.from_user.id):
        return
    channels = list_channels()
    if not channels:
        await message.answer("No channels configured.")
        return
    lines = [f"*Channel {idx}*\n{escape_md(ch.invite_link)}" for idx, ch in enumerate(channels, start=1)]
    await message.answer("\n\n".join(lines), parse_mode="Markdown")


@router.message(Command("removechannel"))
async def remove_channel_command(message: types.Message):
    if message.from_user is None or not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("Usage: /removechannel <chat\\_id>")
        return
    try:
        chat_id = int(parts[1].strip())
    except ValueError:
        await message.answer("chat_id must be an integer")
        return
    channel = get_channel_by_chat_id(chat_id)
    if not channel:
        await message.answer("Channel not found.")
        return
    await message.answer(
        "Do you want to remove this channel?",
        reply_markup=confirm_channel_delete_keyboard(chat_id),
    )


@router.callback_query(F.data.startswith("chdelcancelid:"))
async def channel_delete_cancel(callback: types.CallbackQuery):
    if callback.from_user is None or not is_admin(callback.from_user.id):
        await callback.answer("Not authorized", show_alert=True)
        return
    await callback.answer("Cancelled")
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception as e:
            logging.error(e)
            pass


@router.callback_query(F.data.startswith("chdelokid:"))
async def channel_delete_confirm(callback: types.CallbackQuery):
    chat_id_raw = callback.data.split(":", 1)[1]
    if callback.from_user is None or not is_admin(callback.from_user.id):
        await callback.answer("Not authorized", show_alert=True)
        return
    try:
        chat_id = int(chat_id_raw)
    except ValueError:
        await callback.answer("Invalid channel id.", show_alert=True)
        return
    channel = get_channel_by_chat_id(chat_id)
    if not channel:
        await callback.answer("Channel not found.", show_alert=True)
        return
    service = ChannelLinkService(callback.bot)
    try:
        await service.remove_channel(channel.invite_link)
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    except Exception as e:
        logging.error(e)
        await callback.answer("Failed to remove channel.", show_alert=True)
        return
    await callback.answer("Channel removed", show_alert=True)
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception as e:
            logging.error(e)
            pass


@router.message(Command("cancel"), StateFilter("*"))
async def cancel_process(message: types.Message, state: FSMContext):
    if message.from_user is None or not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("Jarayon bekor qilindi va holat tozalandi.")


@router.message(Command("help"))
async def admin_help(message: types.Message):
    if message.from_user is None or not is_admin(message.from_user.id):
        return
    help_text = (
        "Admin commands:\n"
        "- /add — start adding a new movie (video → name → description → code).\n"
        "- /remove <code> — delete a movie by its code (asks for confirmation).\n"
        "- /addchannel <chat\\_id> <invite\\_link> — register a required channel (bot must be admin).\n"
        "- /channels — list configured required channels.\n"
        "- /removechannel <chat\\_id> — remove a required channel (asks for confirmation).\n"
        "- /cancel — cancel any ongoing process and clear state."
    )
    await message.answer(help_text)
