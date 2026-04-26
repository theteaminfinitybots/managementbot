import html
from typing import Optional, List

from telegram import Update, Bot, User, Chat, Message
from telegram.error import BadRequest
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext
from telegram.utils.helpers import mention_html

from AloneRobot import dispatcher
from AloneRobot.modules.sql import antiflood_sql as sql
from AloneRobot.modules.helper_funcs.chat_status import (
    is_user_admin,
    user_admin,
    can_restrict,
)

FLOOD_GROUP = 3

# 🔥 ADD YOUR BAN IMAGE HERE
BAN_IMG = "https://graph.org/file/f3a0728da34ad80bb1ed6-5c2912a3e77baa8cd2.jpg"


# ================= FLOOD CHECK ================= #
def check_flood(update: Update, context: CallbackContext) -> Optional[str]:
    bot: Bot = context.bot
    user: Optional[User] = update.effective_user
    chat: Optional[Chat] = update.effective_chat
    msg: Optional[Message] = update.effective_message

    if not user:
        return

    # ignore admins
    if is_user_admin(chat, user.id):
        return

    should_ban = sql.update_flood(chat.id, user.id)

    if not should_ban:
        return

    try:
        chat.ban_member(user.id)

        context.bot.send_photo(
            chat_id=chat.id,
            photo=BAN_IMG,
            caption=(
                "🚫 ғʟᴏᴏᴅ ᴅᴇᴛᴇᴄᴛᴇᴅ\n\n"
                f"{mention_html(user.id, user.first_name)} ᴡᴀs ʙᴀɴɴᴇᴅ ғᴏʀ sᴘᴀᴍᴍɪɴɢ."
            ),
            parse_mode="HTML",
        )

        return (
            "<b>{}</b>\n"
            "<b>User:</b> {}\n"
            "Flooded the chat."
        ).format(
            html.escape(chat.title),
            mention_html(user.id, user.first_name),
        )

    except BadRequest:
        msg.reply_text(
            "ɪ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ʙᴀɴ 😐\n"
            "ᴀɴᴛɪғʟᴏᴏᴅ ᴅɪsᴀʙʟᴇᴅ."
        )
        sql.set_flood(chat.id, 0)


# ================= SET FLOOD ================= #
@user_admin
@can_restrict
def set_flood(update: Update, context: CallbackContext) -> Optional[str]:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    args = context.args

    if not args:
        message.reply_text("ᴜsᴀɢᴇ: /setflood <ɴᴜᴍʙᴇʀ/ᴏғғ>")
        return

    val = args[0].lower()

    if val in ["off", "no", "0"]:
        sql.set_flood(chat.id, 0)
        message.reply_text("ᴀɴᴛɪғʟᴏᴏᴅ ᴅɪsᴀʙʟᴇᴅ.")
        return

    if val.isdigit():
        amount = int(val)

        if amount < 3:
            message.reply_text("ᴀɴᴛɪғʟᴏᴏᴅ ᴍɪɴɪᴍᴜᴍ ʟɪᴍɪᴛ ɪs 3.")
            return

        sql.set_flood(chat.id, amount)

        message.reply_text(
            f"ᴀɴᴛɪғʟᴏᴏᴅ sᴇᴛ ᴛᴏ {amount} ᴍᴇssᴀɢᴇs."
        )

        return (
            "<b>{}</b>\n"
            "<b>Admin:</b> {}\n"
            "Set flood to <code>{}</code>"
        ).format(
            html.escape(chat.title),
            mention_html(user.id, user.first_name),
            amount,
        )

    else:
        message.reply_text("ɪɴᴠᴀʟɪᴅ ᴀʀɢᴜᴍᴇɴᴛ.")

# ================= CHECK STATUS ================= #
def flood(update: Update, context: CallbackContext):
    chat = update.effective_chat

    limit = sql.get_flood_limit(chat.id)

    if limit == 0:
        update.effective_message.reply_text(
            "ᴀɴᴛɪғʟᴏᴏᴅ ɪs ᴏғғ."
        )
    else:
        update.effective_message.reply_text(
            f"ᴜsᴇʀ ᴡɪʟʟ ʙᴇ ʙᴀɴɴᴇᴅ ɪғ sᴇɴᴅs ᴍᴏʀᴇ ᴛʜᴀɴ {limit} ᴍᴇssᴀɢᴇs."
        )


# ================= MIGRATION ================= #
def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


# ================= SETTINGS ================= #
def __chat_settings__(chat_id, user_id):
    limit = sql.get_flood_limit(chat_id)

    if limit == 0:
        return "ᴀɴᴛɪғʟᴏᴏᴅ ɪs ᴏғғ."
    else:
        return f"ᴀɴᴛɪғʟᴏᴏᴅ: `{limit}`"


# ================= HANDLERS ================= #
FLOOD_HANDLER = MessageHandler(
    Filters.group & ~Filters.status_update,
    check_flood,
)

SET_FLOOD_HANDLER = CommandHandler(
    "setflood",
    set_flood,
    filters=Filters.group,
)

CHECK_FLOOD_HANDLER = CommandHandler(
    "flood",
    flood,
    filters=Filters.group,
)

dispatcher.add_handler(FLOOD_HANDLER, group=FLOOD_GROUP)
dispatcher.add_handler(SET_FLOOD_HANDLER)
dispatcher.add_handler(CHECK_FLOOD_HANDLER)


# ================= HELP ================= #
__help__ = """
» ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏᴍᴍᴀɴᴅs ꜰᴏʀ Aɴᴛɪ-Fʟᴏᴏᴅ :

Antiflood allows you to take action on users that send more than x messages in a row.
Exceeding the set flood will result in restricting that user.

This will mute users if they send more than 10 messages in a row, bots are ignored.

❍ /flood: Get the current flood control setting

Admins only:
❍ /setflood <int/'no'/'off'>: enables or disables flood control
Example: /setflood 10

❍ /setfloodmode <ban/kick/mute/tban/tmute> <value>:
Action to perform when user have exceeded flood limit.

Note:
Value must be filled for tban and tmute!!

It can be:
5m = 5 minutes
6h = 6 hours
3d = 3 days
1w = 1 week
"""

__mod_name__ = "ᴀɴᴛɪғʟᴏᴏᴅ"

