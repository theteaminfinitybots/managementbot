import asyncio
from platform import python_version as pyver

from pyrogram import __version__ as pver
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram import __version__ as lver
from telethon import __version__ as tver

from AloneRobot import SUPPORT_CHAT, pbot, BOT_USERNAME, OWNER_ID, BOT_NAME

# only 2 photos
PHOTO = [
    "https://graph.org/file/0b1f83450b59a65004800-5fd68e26d8fcc38fed.jpg",
    "https://graph.org/file/5bf10b670c93c624af3e0-6d476603a36e8052b0.jpg",
]

Alone = [
    [
        InlineKeyboardButton(text="👑 ᴏᴡɴᴇʀ", user_id=OWNER_ID),
        InlineKeyboardButton(text="🛠️ ꜱᴜᴘᴘᴏʀᴛ", url=f"https://t.me/{SUPPORT_CHAT}"),
        InlineKeyboardButton(text="🌙 ᴜᴘᴘᴇʀ ᴍᴏᴏɴ", url="https://t.me/dark_musictm"),
    ],
    [
        InlineKeyboardButton(
            text="• ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ •",
            url=f"https://t.me/{BOT_USERNAME}?startgroup=true",
        ),
    ],
]


@pbot.on_message(filters.command("alive"))
async def restart(client, m: Message):
    await m.delete()

    msg = await m.reply("⚡")
    await asyncio.sleep(0.2)
    await msg.edit("ᴅɪɴɢ ᴅᴏɴɢ ꨄ ᴀʟɪᴠᴇ...")
    await asyncio.sleep(0.2)
    await msg.edit("ᴅɪɴɢ ᴅᴏɴɢ ꨄ ᴀʟɪᴠᴇ......")
    await asyncio.sleep(0.2)
    await msg.delete()

    # send photo (random from 2)
    import random
    img = random.choice(PHOTO)

    await m.reply_photo(
        photo=img,
        caption=f"""
**ʜᴇʏ, ɪ ᴀᴍ 『[{BOT_NAME}](https://t.me/{BOT_USERNAME})』**

━━━━━━━━━━━━━━━━━━━
» ᴏᴡɴᴇʀ : [ᴜᴘᴘᴇʀ ᴍᴏᴏɴ](tg://user?id={OWNER_ID})

» ʟɪʙʀᴀʀʏ : `{lver}`
» ᴛᴇʟᴇᴛʜᴏɴ : `{tver}`
» ᴘʏʀᴏɢʀᴀᴍ : `{pver}`
» ᴘʏᴛʜᴏɴ : `{pyver()}`
━━━━━━━━━━━━━━━━━━━

✧ ʙᴏᴛ ɪꜱ ʀᴜɴɴɪɴɢ ꜱᴍᴏᴏᴛʜʟʏ ✧
""",
        reply_markup=InlineKeyboardMarkup(Alone),
    )
