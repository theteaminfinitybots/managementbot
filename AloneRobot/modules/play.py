import asyncio

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    InputMediaPhoto,
)
from pyrogram.enums import ChatMemberStatus

from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped

from AloneRobot import pbot as app
from AloneRobot.modules import Youtube
from config import API_ID, API_HASH, STRING_SESSION, BANNED_USERS


assistant = Client(
    "assistant",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=STRING_SESSION,
)

call = PyTgCalls(assistant)

QUEUE = {}
PLAYING = {}
AUTOPLAY = {}

PREFIX = ["/", "!", "."]

def cmd(cmds):
    return filters.command(cmds, prefixes=PREFIX)


def is_admin(chat_id, user_id):
    try:
        member = app.get_chat_member(chat_id, user_id)
        return member.status in [
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
        ]
    except:
        return False


def buttons(chat_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏸", callback_data=f"pause|{chat_id}"),
            InlineKeyboardButton("▶️", callback_data=f"resume|{chat_id}"),
            InlineKeyboardButton("⏭", callback_data=f"skip|{chat_id}"),
            InlineKeyboardButton("⏹", callback_data=f"stop|{chat_id}")
        ]
    ])

async def start_stream(chat_id, msg=None):

    if chat_id not in QUEUE or not QUEUE[chat_id]:
        return

    data = QUEUE[chat_id][0]

    try:
        file = await YouTube.download(data["link"], msg)
    except:
        return await app.send_message(chat_id, "❌ download failed")

    # FIX: your youtube.py returns (file, True/False)
    if isinstance(file, tuple):
        file, ok = file
        if not ok or not file:
            return await app.send_message(chat_id, "❌ invalid file")

    try:
        await call.join_group_call(chat_id, AudioPiped(file))
    except:
        await call.change_stream(chat_id, AudioPiped(file))

    PLAYING[chat_id] = data


async def next_song(chat_id):

    if chat_id in QUEUE and QUEUE[chat_id]:
        QUEUE[chat_id].pop(0)

    if chat_id in QUEUE and QUEUE[chat_id]:
        await start_stream(chat_id)
        return True

    return False

@app.on_message(cmd("play") & filters.group & ~BANNED_USERS)
async def play(_, message: Message):

    if len(message.command) < 2:
        return await message.reply_text("➻ use /play song name")

    query = message.text.split(None, 1)[1]

    msg = await message.reply_text("🎧 searching...")

    try:
        data, vid = await YouTube.track(query)
    except:
        return await msg.edit("❌ failed to fetch")

    chat_id = message.chat.id

    QUEUE.setdefault(chat_id, []).append(data)
    pos = len(QUEUE[chat_id])

    if pos == 1:
        await start_stream(chat_id, msg)

    await msg.edit_text(
        f"""
🎵 {data['title']}
⏱ {data['duration_min']}
📍 Position: {pos}
"""
        )

@app.on_message(cmd(["skip"]) & filters.group)
async def skip(_, message: Message):

    if not is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ admin only")

    if not await next_song(message.chat.id):
        return await message.reply_text("❌ no next song")

    await message.reply_text("⏭ skipped")


@app.on_message(cmd(["stop"]) & filters.group)
async def stop(_, message: Message):

    if not is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ admin only")

    chat_id = message.chat.id
    QUEUE[chat_id] = []

    try:
        await call.leave_group_call(chat_id)
    except:
        pass

    await message.reply_text("⏹ stopped")


@app.on_message(cmd(["pause"]) & filters.group)
async def pause(_, message: Message):
    if not is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ admin only")

    await call.pause_stream(message.chat.id)
    await message.reply_text("⏸ paused")


@app.on_message(cmd(["resume"]) & filters.group)
async def resume(_, message: Message):
    if not is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ admin only")

    await call.resume_stream(message.chat.id)
    await message.reply_text("▶️ resumed")

@app.on_callback_query(filters.regex("pause"))
async def cb_pause(_, q: CallbackQuery):
    await call.pause_stream(int(q.data.split("|")[1]))
    await q.answer("paused")


@app.on_callback_query(filters.regex("resume"))
async def cb_resume(_, q: CallbackQuery):
    await call.resume_stream(int(q.data.split("|")[1]))
    await q.answer("resumed")


@app.on_callback_query(filters.regex("skip"))
async def cb_skip(_, q: CallbackQuery):

    chat_id = int(q.data.split("|")[1])

    await next_song(chat_id)
    await q.answer("skipped")


@app.on_callback_query(filters.regex("stop"))
async def cb_stop(_, q: CallbackQuery):

    chat_id = int(q.data.split("|")[1])
    QUEUE[chat_id] = []

    try:
        await call.leave_group_call(chat_id)
    except:
        pass

    await q.answer("stopped")


@call.on_stream_end()
async def stream_end(_, update):

    chat_id = update.chat_id

    if await next_song(chat_id):
        return

    if AUTOPLAY.get(chat_id):
        results = await YouTube.search("music trending songs", limit=5)

        if results:
            data = {
                "title": results[0]["title"],
                "duration_min": results[0]["duration"],
                "link": results[0]["link"],
                "thumb": results[0]["thumbnails"][0]["url"],
            }

            QUEUE.setdefault(chat_id, []).append(data)
            await start_stream(chat_id)
            return

    try:
        await call.leave_group_call(chat_id)
    except:
        pass
