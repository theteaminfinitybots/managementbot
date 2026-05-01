import html
from typing import Optional

from telegram import Update, Chat, User, Message, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CallbackQueryHandler

from AloneRobot import dispatcher
from AloneRobot.modules.connection import connected
from AloneRobot.modules.disable import DisableAbleCommandHandler
from AloneRobot.modules.helper_funcs.chat_status import user_admin
from AloneRobot.modules.helper_funcs.alternate import send_message
from AloneRobot.modules.log_channel import loggable

import AloneRobot.modules.sql.joinreq_sql as sql


@user_admin
def joinrequest(update: Update, context: CallbackContext):
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

    state = sql.get_joinreq(chat_id)
    status = "ᴇɴᴀʙʟᴇᴅ" if state else "ᴅɪsᴀʙʟᴇᴅ"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ᴇɴᴀʙʟᴇ", callback_data=f"joinreq_on_{chat_id}"),
            InlineKeyboardButton("ᴅɪsᴀʙʟᴇ", callback_data=f"joinreq_off_{chat_id}")
        ]
    ])

    send_message(
        msg,
        "ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ ɪs ᴄᴜʀʀᴇɴᴛʟʏ *{}* ɪɴ *{}*.".format(status, chat_name),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard,
    )


def joinreq_button(update: Update, context: CallbackContext):
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
        sql.set_joinreq(chat_id, True)
        text = "ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ ʜᴀs ʙᴇᴇɴ *ᴇɴᴀʙʟᴇᴅ*."
    else:
        sql.set_joinreq(chat_id, False)
        text = "ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ ʜᴀs ʙᴇᴇɴ *ᴅɪsᴀʙʟᴇᴅ*."

    query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)


def joinreq_notify(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user

    if not sql.get_joinreq(chat.id):
        return

    text = "ɴᴇᴡ ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛ:\n\n"
    text += "• ɴᴀᴍᴇ: {}\n".format(html.escape(user.first_name))
    text += "• ɪᴅ: <code>{}</code>\n".format(user.id)
    if user.username:
        text += "• ᴜsᴇʀɴᴀᴍᴇ: @{}\n".format(user.username)

    context.bot.send_message(chat.id, text, parse_mode=ParseMode.HTML)


__help__ = """
ᴍᴀɴᴀɢᴇ ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛs ɪɴ ɢʀᴏᴜᴘs.

 ❍ /joinrequest : ᴏᴘᴇɴ ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ  
"""

__mod_name__ = "ᴊᴏɪɴ-ʀᴇǫ"


JOINREQ_HANDLER = DisableAbleCommandHandler("joinrequest", joinrequest, run_async=True)

dispatcher.add_handler(JOINREQ_HANDLER)
dispatcher.add_handler(CallbackQueryHandler(joinreq_button, pattern=r"joinreq_"))
