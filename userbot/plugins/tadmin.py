"""
idea from lynda and rose bot
made by @mrconfused
"""
from telethon.errors import BadRequestError
from telethon.errors.rpcerrorlist import UserAdminInvalidError, UserIdInvalidError
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights
from telethon.utils import get_display_name

from userbot import catub

from ..core.managers import edit_or_reply
from ..helpers.utils import _format
from . import BOTLOG, BOTLOG_CHATID, extract_time, get_user_from_event

plugin_category = "admin"

# =================== CONSTANT ===================
NO_ADMIN = "`Я не админ!`"
NO_PERM = "`У меня недостаточно прав! Это так грустно.`"


@catub.cat_cmd(
    pattern="tmute(?:\s|$)([\s\S]*)",
    command=("tmute", plugin_category),
    info={
        "заголовок": "Чтобы запретить отправку сообщений для этого пользователя",
        "описание": "Temporary mutes the user for given time.",
        "Единицы времени": {
            "s": "seconds",
            "m": "minutes",
            "h": "Hours",
            "d": "days",
            "w": "weeks",
        },
        "Применение": [
            "{tr}tmute <userid/username/reply> <time>",
            "{tr}tmute <userid/username/reply> <time> <reason>",
        ],
        "Примеры": ["{tr}tmute 2d to test muting for 2 days"],
    },
    groups_only=True,
    require_admin=True,
)
async def tmuter(event):  # sourcery no-metrics
    "Чтобы отключить человека на определенное время"
    catevent = await edit_or_reply(event, "`muting....`")
    user, reason = await get_user_from_event(event, catevent)
    if not user:
        return
    if not reason:
        return await catevent.edit("вы не упомянули время, проверьте `.help tmute`")
    reason = reason.split(" ", 1)
    hmm = len(reason)
    cattime = reason[0].strip()
    reason = "".join(reason[1:]) if hmm > 1 else None
    ctime = await extract_time(catevent, cattime)
    if not ctime:
        return
    if user.id == event.client.uid:
        return await catevent.edit("Извините, я не могу ввыдать мут")
    try:
        await catevent.client(
            EditBannedRequest(
                event.chat_id,
                user.id,
                ChatBannedRights(until_date=ctime, send_messages=True),
            )
        )
        # Announce that the function is done
        if reason:
            await catevent.edit(
                f"{_format.mentionuser(user.first_name ,user.id)} был замучен в {get_display_name(await event.get_chat())}\n"
                f"**Отключено для : **{cattime}\n"
                f"**Причина : **__{reason}__"
            )
            if BOTLOG:
                await event.client.send_message(
                    BOTLOG_CHATID,
                    "#TMUTE\n"
                    f"**Пользователь : **[{user.first_name}](tg://user?id={user.id})\n"
                    f"**Чат : **{get_display_name(await event.get_chat())}(`{event.chat_id}`)\n"
                    f"**Замчен на : **`{cattime}`\n"
                    f"**Причина : **`{reason}``",
                )
        else:
            await catevent.edit(
                f"{_format.mentionuser(user.first_name ,user.id)} был замучен в {get_display_name(await event.get_chat())}\n"
                f"Замчен на {cattime}\n"
            )
            if BOTLOG:
                await event.client.send_message(
                    BOTLOG_CHATID,
                    "#TMUTE\n"
                    f"**Пользователь : **[{user.first_name}](tg://user?id={user.id})\n"
                    f"**Чат : **{get_display_name(await event.get_chat())}(`{event.chat_id}`)\n"
                    f"**Замчен на : **`{cattime}`",
                )
        # Announce to logging group
    except UserIdInvalidError:
        return await catevent.edit("`Ой, моя немая логика сломалась!`")
    except UserAdminInvalidError:
        return await catevent.edit(
            "`Либо вы не администратор, либо пытались отключить администратора, которого не повышали`"
        )
    except Exception as e:
        return await catevent.edit(f"`{e}`")


@catub.cat_cmd(
    pattern="tban(?:\s|$)([\s\S]*)",
    command=("tban", plugin_category),
    info={
        "заголовок": "Чтобы удалить пользователя из группы на указанное время.",
        "описание": "Временная блокировка пользователя на заданное время.",
        "Единицы времени": {
            "s": "seconds",
            "m": "minutes",
            "h": "Hours",
            "d": "days",
            "w": "weeks",
        },
        "Применение": [
            "{tr}tban <userid/username/reply> <time>",
            "{tr}tban <userid/username/reply> <time> <reason>",
        ],
        "Примеры": ["{tr}tban 2d to test baning for 2 days"],
    },
    groups_only=True,
    require_admin=True,
)
async def tban(event):  # sourcery no-metrics
    "Забанить человека на определенное время"
    catevent = await edit_or_reply(event, "`банн....`")
    user, reason = await get_user_from_event(event, catevent)
    if not user:
        return
    if not reason:
        return await catevent.edit("вы не упомянули время, проверьте `.help tban`")
    reason = reason.split(" ", 1)
    hmm = len(reason)
    cattime = reason[0].strip()
    reason = "".join(reason[1:]) if hmm > 1 else None
    ctime = await extract_time(catevent, cattime)
    if not ctime:
        return
    if user.id == event.client.uid:
        return await catevent.edit("Извините, я не могу забанить себя")
    await catevent.edit("`Уничтожение вредителя!`")
    try:
        await event.client(
            EditBannedRequest(
                event.chat_id,
                user.id,
                ChatBannedRights(until_date=ctime, view_messages=True),
            )
        )
    except UserAdminInvalidError:
        return await catevent.edit(
            "`Либо вы не админ, либо пытались забанить админа, которого не продвигали`"
        )
    except BadRequestError:
        return await catevent.edit(NO_PERM)
    # Helps ban group join spammers more easily
    try:
        reply = await event.get_reply_message()
        if reply:
            await reply.delete()
    except BadRequestError:
        return await catevent.edit(
            "`У меня нет прав на уничтожение сообщений! Но все равно его запретили!`"
        )
    # Delete message and then tell that the command
    # is done gracefully
    # Shout out the ID, so that fedadmins can fban later
    if reason:
        await catevent.edit(
            f"{_format.mentionuser(user.first_name ,user.id)} был забанен в {get_display_name(await event.get_chat())}\n"
            f"забанен на {cattime}\n"
            f"Причина:`{reason}`"
        )
        if BOTLOG:
            await event.client.send_message(
                BOTLOG_CHATID,
                "#TBAN\n"
                f"**Пользователь : **[{user.first_name}](tg://user?id={user.id})\n"
                f"**Чат : **{get_display_name(await event.get_chat())}(`{event.chat_id}`)\n"
                f"**Забанен до : **`{cattime}`\n"
                f"**Причина : **__{reason}__",
            )
    else:
        await catevent.edit(
            f"{_format.mentionuser(user.first_name ,user.id)} был забанен в {get_display_name(await event.get_chat())}\n"
            f"забанен на {cattime}\n"
        )
        if BOTLOG:
            await event.client.send_message(
                BOTLOG_CHATID,
                "#TBAN\n"
                f"**Пользователь : **[{user.first_name}](tg://user?id={user.id})\n"
                f"**Чат : **{get_display_name(await event.get_chat())}(`{event.chat_id}`)\n"
                f"**Забанен до : **`{cattime}`",
            )
