import asyncio
import time
import requests
from typing import Dict, List

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto
)

from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio
from pytgcalls.types.stream import StreamAudioEnded

from AloneRobot.config import API_ID, API_HASH, STRING_SESSION

JIOSAAVN_API = "https://your-api.com/search?q="
PROCESS_IMG = "https://your-image-link.jpg"

assistant = Client(
    "vc-assistant",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=STRING_SESSION,
)

app = Client("AloneRobot")
pytgcalls = PyTgCalls(assistant)

QUEUE: Dict[int, List[dict]] = {}
START_TIME = {}
LOOP = {}
AUTOPLAY = {}

def fetch_song(query: str):
    try:
        r = requests.get(JIOSAAVN_API + query).json()
        return {
            "title": r["title"],
            "url": r["url"],
            "thumb": r.get("thumbnail", ""),
            "duration": r.get("duration", 0)
        }
    except:
        return None

def buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏯", "pause"),
            InlineKeyboardButton("⏭", "skip"),
            InlineKeyboardButton("⏹", "end"),
        ],
        [
            InlineKeyboardButton("🔁", "loop"),
            InlineKeyboardButton("🔄", "autoplay"),
        ]
    ])

async def play_stream(chat_id: int, seek: int = 0):
    if chat_id not in QUEUE or not QUEUE[chat_id]:
        return await pytgcalls.leave_group_call(chat_id)

    song = QUEUE[chat_id][0]

    await pytgcalls.join_group_call(
        chat_id,
        AudioPiped(song["url"], HighQualityAudio(), seek=seek),
    )

    START_TIME[chat_id] = time.time() - seek

async def next_track(chat_id: int):
    if LOOP.get(chat_id, 0) > 0:
        LOOP[chat_id] -= 1
    else:
        if chat_id in QUEUE and QUEUE[chat_id]:
            QUEUE[chat_id].pop(0)

    if chat_id in QUEUE and QUEUE[chat_id]:
        await play_stream(chat_id)
    else:
        await pytgcalls.leave_group_call(chat_id)

@pytgcalls.on_stream_end()
async def stream_end(_, update: StreamAudioEnded):
    await next_track(update.chat_id)

async def seek_stream(chat_id: int, sec: int):
    if chat_id not in START_TIME:
        return

    pos = int(time.time() - START_TIME[chat_id]) + sec
    if pos < 0:
        pos = 0

    await play_stream(chat_id, seek=pos)

def add(chat_id: int, song: dict):
    QUEUE.setdefault(chat_id, [])
    QUEUE[chat_id].append(song)

def clear(chat_id: int):
    QUEUE[chat_id] = []

@app.on_message(filters.command("play"))
async def play(_, message: Message):
    chat_id = message.chat.id
    query = " ".join(message.command[1:])

    if not query:
        return await message.reply("Give song name")

    try:
        await message.delete()
    except:
        pass

    processing = await app.send_photo(
        chat_id,
        PROCESS_IMG,
        caption="⏳ Processing..."
    )

    song = fetch_song(query)

    if not song:
        return await processing.edit_caption("❌ Not found")

    add(chat_id, song)

    if len(QUEUE[chat_id]) == 1:
        await play_stream(chat_id)

        try:
            await processing.edit_media(
                media=InputMediaPhoto(
                    media=song["thumb"],
                    caption=f"▶️ {song['title']}"
                ),
                reply_markup=buttons()
            )
        except:
            await processing.delete()
            await app.send_photo(
                chat_id,
                song["thumb"],
                caption=f"▶️ {song['title']}",
                reply_markup=buttons()
            )
    else:
        await processing.edit_caption(f"➕ Added: {song['title']}")

@app.on_message(filters.command("skip"))
async def skip(_, message: Message):
    chat_id = message.chat.id

    if chat_id not in QUEUE or not QUEUE[chat_id]:
        return await message.reply("Empty")

    try:
        n = int(message.command[1])
    except:
        n = 1

    n = min(n, len(QUEUE[chat_id]))

    for _ in range(n):
        QUEUE[chat_id].pop(0)

    if QUEUE[chat_id]:
        await play_stream(chat_id)
        await message.reply(f"Skipped {n}")
    else:
        await pytgcalls.leave_group_call(chat_id)
        await message.reply("Ended")

@app.on_message(filters.command("pause"))
async def pause(_, m: Message):
    await pytgcalls.pause_stream(m.chat.id)
    await m.reply("Paused")

@app.on_message(filters.command("resume"))
async def resume(_, m: Message):
    await pytgcalls.resume_stream(m.chat.id)
    await m.reply("Resumed")

@app.on_message(filters.command("end"))
async def end(_, m: Message):
    clear(m.chat.id)
    await pytgcalls.leave_group_call(m.chat.id)
    await m.reply("Stopped")

@app.on_message(filters.command("seek"))
async def seek_cmd(_, m: Message):
    try:
        sec = int(m.command[1])
    except:
        return await m.reply("Usage: /seek 30")

    await seek_stream(m.chat.id, sec)
    await m.reply(f"+{sec}s")

@app.on_message(filters.command("seekback"))
async def seek_back(_, m: Message):
    try:
        sec = int(m.command[1])
    except:
        return await m.reply("Usage: /seekback 10")

    await seek_stream(m.chat.id, -sec)
    await m.reply(f"-{sec}s")

@app.on_message(filters.command("loop"))
async def loop(_, m: Message):
    try:
        LOOP[m.chat.id] = int(m.command[1])
    except:
        return await m.reply("Usage: /loop 3")

    await m.reply(f"Loop {LOOP[m.chat.id]}")

@app.on_message(filters.command("autoplay"))
async def auto(_, m: Message):
    cid = m.chat.id
    AUTOPLAY[cid] = not AUTOPLAY.get(cid, False)
    await m.reply(f"Autoplay {AUTOPLAY[cid]}")

@app.on_callback_query()
async def cb(_, q):
    cid = q.message.chat.id

    if q.data == "pause":
        await pytgcalls.pause_stream(cid)

    elif q.data == "skip":
        if QUEUE.get(cid):
            QUEUE[cid].pop(0)
            await play_stream(cid)

    elif q.data == "end":
        clear(cid)
        await pytgcalls.leave_group_call(cid)

    elif q.data == "loop":
        LOOP[cid] = LOOP.get(cid, 0) + 1

    elif q.data == "autoplay":
        AUTOPLAY[cid] = not AUTOPLAY.get(cid, False)

    await q.answer("OK")

async def main():
    await assistant.start()
    await app.start()
    await pytgcalls.start()

asyncio.get_event_loop().run_until_complete(main())
asyncio.get_event_loop().run_forever()
