import asyncio
import os

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, CallbackQuery

from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped

from AloneRobot import app
from config import API_ID, API_HASH, STRING_SESSION, BANNED_USERS

from yt import YouTubeAPI

yt = YouTubeAPI()

assistant = Client(
    "assistant",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=STRING_SESSION,
)

call = PyTgCalls(assistant)

QUEUE = {}
AUTOPLAY = {}
PLAYING = {}

def buttons(chat_id):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏸", callback_data=f"pause|{chat_id}"),
                InlineKeyboardButton("▶️", callback_data=f"resume|{chat_id}"),
                InlineKeyboardButton("⏭", callback_data=f"skip|{chat_id}"),
                InlineKeyboardButton("⏹", callback_data=f"stop|{chat_id}")
            ],
            [
                InlineKeyboardButton("🔁 autoplay", callback_data=f"autoplay|{chat_id}")
            ]
        ]
    )

async def download(url):
    os.makedirs("downloads", exist_ok=True)
    file = f"downloads/{url.split('=')[-1]}.mp3"

    if os.path.exists(file):
        return file

    proc = await asyncio.create_subprocess_shell(
        f'yt-dlp -x --audio-format mp3 -o "{file}" {url}'
    )
    await proc.communicate()

    return file

async def join(chat_id, file):
    try:
        await call.join_group_call(chat_id, AudioPiped(file))
    except:
        await call.change_stream(chat_id, AudioPiped(file))

async def play_stream(chat_id):
    if chat_id not in QUEUE or not QUEUE[chat_id]:
        return

    data = QUEUE[chat_id][0]

    file = await download(data["link"])

    await join(chat_id, file)

    PLAYING[chat_id] = data

@app.on_message(filters.command("play") & filters.group & ~BANNED_USERS)
async def play(_, message: Message):

    if len(message.command) < 2:
        return await message.reply_text("➻ ᴜsᴇ /play song")

    query = message.text.split(None, 1)[1]

    msg = await message.reply_photo(
        photo="https://graph.org/file/40f0822f02594343090cc-030776a6e3c7f31e9d.jpg",
        caption="➻ ᴘʀᴏᴄᴇssɪɴɢ..."
    )

    try:
        data, _ = await yt.track(query)
    except:
        return await msg.edit_text("❌ error")

    chat_id = message.chat.id

    QUEUE.setdefault(chat_id, []).append(data)

    pos = len(QUEUE[chat_id])

    if pos == 1:
        await play_stream(chat_id)

    caption = f"""
➻ ᴛɪᴛʟᴇ: {data['title']}
➻ ᴅᴜʀᴀᴛɪᴏɴ: {data['duration_min']}
➻ ᴘᴏsɪᴛɪᴏɴ: {pos}
➻ ʙʏ: {message.from_user.first_name}
"""

    await msg.edit_media(
        InputMediaPhoto(
            media=data["thumb"],
            caption=caption
        ),
        reply_markup=buttons(chat_id)
    )

@app.on_message(filters.command("skip") & filters.group)
async def skip(_, message: Message):
    chat_id = message.chat.id

    if chat_id not in QUEUE or len(QUEUE[chat_id]) <= 1:
        return await message.reply_text("❌ no next song")

    QUEUE[chat_id].pop(0)

    await play_stream(chat_id)

    await message.reply_text("⏭ skipped")


@app.on_message(filters.command("stop") & filters.group)
async def stop(_, message: Message):
    chat_id = message.chat.id

    QUEUE[chat_id] = []

    await call.leave_group_call(chat_id)

    await message.reply_text("⏹ stopped")


@app.on_message(filters.command("end") & filters.group)
async def end(_, message: Message):
    chat_id = message.chat.id

    QUEUE[chat_id] = []

    await call.leave_group_call(chat_id)

    await message.reply_text("⏹ queue ended")


@app.on_message(filters.command("pause") & filters.group)
async def pause(_, message: Message):
    chat_id = message.chat.id
    await call.pause_stream(chat_id)
    await message.reply_text("⏸ paused")


@app.on_message(filters.command("resume") & filters.group)
async def resume(_, message: Message):
    chat_id = message.chat.id
    await call.resume_stream(chat_id)
    await message.reply_text("▶️ resumed")


@app.on_message(filters.command("reload") & filters.group)
async def reload(_, message: Message):
    QUEUE.clear()
    AUTOPLAY.clear()
    PLAYING.clear()
    await message.reply_text("🔄 reloaded")

@app.on_callback_query(filters.regex("pause"))
async def cb_pause(_, q: CallbackQuery):
    chat_id = int(q.data.split("|")[1])
    await call.pause_stream(chat_id)
    await q.answer("paused")


@app.on_callback_query(filters.regex("resume"))
async def cb_resume(_, q: CallbackQuery):
    chat_id = int(q.data.split("|")[1])
    await call.resume_stream(chat_id)
    await q.answer("resumed")


@app.on_callback_query(filters.regex("skip"))
async def cb_skip(_, q: CallbackQuery):
    chat_id = int(q.data.split("|")[1])

    if len(QUEUE.get(chat_id, [])) <= 1:
        return await q.answer("no next", show_alert=True)

    QUEUE[chat_id].pop(0)

    await play_stream(chat_id)

    await q.answer("skipped")


@app.on_callback_query(filters.regex("stop"))
async def cb_stop(_, q: CallbackQuery):
    chat_id = int(q.data.split("|")[1])

    QUEUE[chat_id] = []

    await call.leave_group_call(chat_id)

    await q.answer("stopped")


@app.on_callback_query(filters.regex("autoplay"))
async def cb_autoplay(_, q: CallbackQuery):
    chat_id = int(q.data.split("|")[1])

    AUTOPLAY[chat_id] = not AUTOPLAY.get(chat_id, False)

    await q.answer(f"autoplay {'on' if AUTOPLAY[chat_id] else 'off'}")

@call.on_stream_end()
async def stream_end(_, update):
    chat_id = update.chat_id

    if chat_id in QUEUE and QUEUE[chat_id]:
        QUEUE[chat_id].pop(0)

    if chat_id in QUEUE and QUEUE[chat_id]:
        await play_stream(chat_id)

    elif AUTOPLAY.get(chat_id):
        results = await yt.search("trending songs", limit=5)

        data = {
            "title": results[0]["title"],
            "duration_min": results[0]["duration"],
            "link": results[0]["link"],
            "thumb": results[0]["thumbnails"][0]["url"]
        }

        QUEUE.setdefault(chat_id, []).append(data)

        await play_stream(chat_id)

    else:
        await call.leave_group_call(chat_id)

        try:
            await app.send_message(chat_id, "➻ stream ended no queued chats !")
        except:
            pass


async def start():
    await assistant.start()
    await call.start()

asyncio.get_event_loop().run_until_complete(start())

