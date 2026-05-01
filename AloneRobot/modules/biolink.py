import re
import html
from typing import Optional

from telegram import Update, Chat, User, Message, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CallbackQueryHandler

from AloneRobot import dispatcher
from AloneRobot.modules.connection import connected
from AloneRobot.modules.disable import DisableAbleCommandHandler
from AloneRobot.modules.helper_funcs.chat_status import user_admin, user_not_admin
from AloneRobot.modules.helper_funcs.alternate import send_message
from AloneRobot.modules.log_channel import loggable

import AloneRobot.modules.sql.biolink_sql as sql


def has_biolink(user: User) -> bool:
    if not user or not user.bio:
        return False
    bio = user.bio.lower()
    if re.search(r"(https?://|t\.me/|@)", bio):
        return True
    return False


@user_admin
def biolink(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if chat.type == "private":
            send_message(msg, "ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴡᴏʀᴋs ᴏɴʟʏ ɪɴ ɢʀᴏᴜᴘs.")
            return
        chat_id = chat.id
        chat_name = chat.title

    state = sql.get_biolink(chat_id)
    status = "ᴇɴᴀʙʟᴇᴅ" if state else "ᴅɪsᴀʙʟᴇᴅ"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ᴇɴᴀʙʟᴇ", callback_data=f"biolink_on_{chat_id}"),
            InlineKeyboardButton("ᴅɪsᴀʙʟᴇ", callback_data=f"biolink_off_{chat_id}")
        ]
    ])

    send_message(
        msg,
        "ʙɪᴏ ʟɪɴᴋ ғɪʟᴛᴇʀ ɪs ᴄᴜʀʀᴇɴᴛʟʏ *{}* ɪɴ *{}*.".format(status, chat_name),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard,
    )


def biolink_button(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user

    data = query.data.split("_")
    action = data[1]
    chat_id = int(data[2])

    try:
        member = context.bot.get_chat_member(chat_id, user.id)
        if member.status not in ["administrator", "creator"]:
            query.answer("ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ.", show_alert=True)
            return
    except:
        query.answer("ᴇʀʀᴏʀ.", show_alert=True)
        return

    if action == "on":
        sql.set_biolink(chat_id, True)
        text = "ʙɪᴏ ʟɪɴᴋ ғɪʟᴛᴇʀ ʜᴀs ʙᴇᴇɴ *ᴇɴᴀʙʟᴇᴅ*."
    else:
        sql.set_biolink(chat_id, False)
        text = "ʙɪᴏ ʟɪɴᴋ ғɪʟᴛᴇʀ ʜᴀs ʙᴇᴇɴ *ᴅɪsᴀʙʟᴇᴅ*."

    query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)


@user_admin
def biofree(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat

    if not msg.reply_to_message:
        send_message(msg, "ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ.")
        return

    user_id = msg.reply_to_message.from_user.id
    sql.add_biofree(chat.id, user_id)

    send_message(msg, "ᴜsᴇʀ ᴀᴅᴅᴇᴅ ᴛᴏ ʙɪᴏ ғʀᴇᴇ ʟɪsᴛ.")


@user_admin
def biounfree(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat

    if not msg.reply_to_message:
        send_message(msg, "ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ.")
        return

    user_id = msg.reply_to_message.from_user.id
    sql.rm_biofree(chat.id, user_id)

    send_message(msg, "ᴜsᴇʀ ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ʙɪᴏ ғʀᴇᴇ ʟɪsᴛ.")


def biofreelist(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat

    users = sql.get_biofree_users(chat.id)

    if not users:
        send_message(msg, "ɴᴏ ᴜsᴇʀs ᴀʀᴇ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ.")
        return

    text = "ʙɪᴏ ғʀᴇᴇ ᴜsᴇʀs:\n"
    for user_id in users:
        text += f"• <code>{user_id}</code>\n"

    send_message(msg, text, parse_mode=ParseMode.HTML)


@user_not_admin
def check_bio(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if not sql.get_biolink(chat.id):
        return

    if sql.is_biofree(chat.id, user.id):
        return

    try:
        member = context.bot.get_chat_member(chat.id, user.id)
        if member.user.is_bot:
            return
    except:
        return

    if has_biolink(user):
        try:
            message.delete()
            context.bot.kick_chat_member(chat.id, user.id)
            context.bot.unban_chat_member(chat.id, user.id)
            context.bot.sendMessage(
                chat.id,
                "ᴜsᴇʀ ᴋɪᴄᴋᴇᴅ ғᴏʀ ʜᴀᴠɪɴɢ ʟɪɴᴋ ɪɴ ʙɪᴏ.",
            )
        except:
            pass


__help__ = """
ʙɪᴏ ʟɪɴᴋ ғɪʟᴛᴇʀ ᴅᴇᴛᴇᴄᴛs ʟɪɴᴋs ᴏʀ @ᴜsᴇʀɴᴀᴍᴇs ɪɴ ᴜsᴇʀ ʙɪᴏ.

 ❍ /biolink : ᴏᴘᴇɴ ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ  
 ❍ /biofree : ᴀᴜᴛʜᴏʀɪᴢᴇ ᴜsᴇʀ  
 ❍ /biounfree : ʀᴇᴍᴏᴠᴇ ᴜsᴇʀ  
 ❍ /biofreelist : ʟɪsᴛ ᴜsᴇʀs  
"""

__mod_name__ = "ʙɪᴏ-ʟɪɴᴋ"


BIOLINK_HANDLER = DisableAbleCommandHandler("biolink", biolink, run_async=True)
BIOFREE_HANDLER = DisableAbleCommandHandler("biofree", biofree, run_async=True)
BIOUNFREE_HANDLER = DisableAbleCommandHandler("biounfree", biounfree, run_async=True)
BIOFREELIST_HANDLER = DisableAbleCommandHandler("biofreelist", biofreelist, run_async=True)

dispatcher.add_handler(BIOLINK_HANDLER)
dispatcher.add_handler(BIOFREE_HANDLER)
dispatcher.add_handler(BIOUNFREE_HANDLER)
dispatcher.add_handler(BIOFREELIST_HANDLER)
dispatcher.add_handler(CallbackQueryHandler(biolink_button, pattern=r"biolink_"))
