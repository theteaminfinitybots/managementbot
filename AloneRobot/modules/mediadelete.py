import time
from datetime import timedelta

from telegram import Update, ParseMode
from telegram.ext import CallbackContext, MessageHandler, Filters

from AloneRobot import dispatcher
from AloneRobot.modules.disable import DisableAbleCommandHandler
from AloneRobot.modules.helper_funcs.chat_status import user_admin
from AloneRobot.modules.helper_funcs.alternate import send_message
from AloneRobot.modules.helper_funcs.string_handling import extract_time

import AloneRobot.modules.sql.mediadel_sql as sql


@user_admin
def mediadelete(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    args = context.args

    if not args:
        send_message(msg, "ᴜsᴇ /mediadelete on ᴏʀ off")
        return

    if args[0].lower() == "on":
        sql.set_mediadel(chat.id, True)
        send_message(msg, "ᴍᴇᴅɪᴀ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ *ᴇɴᴀʙʟᴇᴅ*.", parse_mode=ParseMode.MARKDOWN)

    elif args[0].lower() == "off":
        sql.set_mediadel(chat.id, False)
        send_message(msg, "ᴍᴇᴅɪᴀ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ *ᴅɪsᴀʙʟᴇᴅ*.", parse_mode=ParseMode.MARKDOWN)

    else:
        send_message(msg, "ᴜsᴇ /mediadelete on ᴏʀ off")


@user_admin
def setmediadelay(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    args = context.args

    if not args:
        send_message(msg, "ᴘʀᴏᴠɪᴅᴇ ᴛɪᴍᴇ. ᴇx: 5m, 1h")
        return

    value = args[0]
    sql.set_delay(chat.id, value)

    send_message(
        msg,
        "ᴍᴇᴅɪᴀ ᴅᴇʟᴇᴛᴇ ᴅᴇʟᴀʏ sᴇᴛ ᴛᴏ *{}*.".format(value),
        parse_mode=ParseMode.MARKDOWN,
    )


def mediastatus(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat

    state = sql.get_mediadel(chat.id)
    delay = sql.get_delay(chat.id)

    status = "ᴇɴᴀʙʟᴇᴅ" if state else "ᴅɪsᴀʙʟᴇᴅ"

    send_message(
        msg,
        "ᴍᴇᴅɪᴀ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ: *{}*\nᴅᴇʟᴀʏ: *{}*".format(status, delay or "ɴᴏɴᴇ"),
        parse_mode=ParseMode.MARKDOWN,
    )


def auto_delete_media(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat

    if not sql.get_mediadel(chat.id):
        return

    if not (
        message.photo
        or message.video
        or message.sticker
        or message.animation
    ):
        return

    delay = sql.get_delay(chat.id)

    try:
        seconds = extract_time(message, delay) if delay else None
    except:
        seconds = None

    if not seconds:
        seconds = int(time.time()) + 10

    context.job_queue.run_once(
        delete_msg,
        when=seconds - int(time.time()),
        context={"chat_id": chat.id, "message_id": message.message_id},
    )


def delete_msg(context: CallbackContext):
    job = context.job
    try:
        context.bot.delete_message(
            job.context["chat_id"],
            job.context["message_id"],
        )
    except:
        pass


__help__ = """
ᴍᴇᴅɪᴀ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ sʏsᴛᴇᴍ.

» /mediadelete on – ᴇɴᴀʙʟᴇ  
» /mediadelete off – ᴅɪsᴀʙʟᴇ  
» /setmediadelay 5m / 1h  
» /mediastatus  

ᴅᴇʟᴇᴛᴇs ᴘʜᴏᴛᴏs, ᴠɪᴅᴇᴏs, sᴛɪᴄᴋᴇʀs & ɢɪғs ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ.
"""

__mod_name__ = "ᴍᴇᴅɪᴀ-ᴅᴇʟᴇᴛᴇ"


MEDIADEL_HANDLER = DisableAbleCommandHandler("mediadelete", mediadelete, run_async=True)
SET_DELAY_HANDLER = DisableAbleCommandHandler("setmediadelay", setmediadelay, run_async=True)
MEDIASTATUS_HANDLER = DisableAbleCommandHandler("mediastatus", mediastatus, run_async=True)

MEDIA_WATCHER = MessageHandler(Filters.all, auto_delete_media, run_async=True)

dispatcher.add_handler(MEDIADEL_HANDLER)
dispatcher.add_handler(SET_DELAY_HANDLER)
dispatcher.add_handler(MEDIASTATUS_HANDLER)
dispatcher.add_handler(MEDIA_WATCHER)
