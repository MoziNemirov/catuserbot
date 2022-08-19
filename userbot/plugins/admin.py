import contextlib

from telethon.errors import (
    BadRequestError,
    ImageProcessFailedError,
    PhotoCropSizeSmallError,
)
from telethon.errors.rpcerrorlist import UserAdminInvalidError, UserIdInvalidError
from telethon.tl.functions.channels import (
    EditAdminRequest,
    EditBannedRequest,
    EditPhotoRequest,
)
from telethon.tl.types import (
    ChatAdminRights,
    ChatBannedRights,
    InputChatPhotoEmpty,
    MessageMediaPhoto,
)
from telethon.utils import get_display_name

from userbot import catub

from ..core.data import _sudousers_list
from ..core.logger import logging
from ..core.managers import edit_delete, edit_or_reply
from ..helpers import media_type
from ..helpers.utils import _format, get_user_from_event
from ..sql_helper.mute_sql import is_muted, mute, unmute
from . import BOTLOG, BOTLOG_CHATID

# =================== STRINGS ============
PP_TOO_SMOL = "`Изображение слишком маленькое`"
PP_ERROR = "`Сбой при обработке изображения`"
NO_ADMIN = "`Я не админ нуб нибба!`"
NO_PERM = "`У меня недостаточно прав! Это так грустно.`"
CHAT_PP_CHANGED = "`Изображение чата изменено`"
INVALID_MEDIA = "`Недопустимое расширение`"

BANNED_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True,
)

UNBAN_RIGHTS = ChatBannedRights(
    until_date=None,
    send_messages=None,
    send_media=None,
    send_stickers=None,
    send_gifs=None,
    send_games=None,
    send_inline=None,
    embed_links=None,
)

LOGS = logging.getLogger(__name__)
MUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=True)
UNMUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=False)

plugin_category = "admin"
# ================================================


@catub.cat_cmd(
    pattern="gpic( -s| -d)$",
    command=("gpic", plugin_category),
    info={
        "заголовок": "Для изменения группового отображаемого изображения или удаления отображаемого изображения",
        "описание": "Ответ на изображение для изменения отображаемой картинки",
        "флаги": {
            "-s": "Чтобы установить групповое изображение",
            "-d": "Чтобы удалить групповое изображение",
        },
        "Применение": [
            "{tr}gpic -s <reply to image>",
            "{tr}gpic -d",
        ],
    },
    groups_only=True,
    require_admin=True,
)
async def set_group_photo(event):  # sourcery no-metrics
    "Для изменения группы dp"
    flag = (event.pattern_match.group(1)).strip()
    if flag == "-s":
        replymsg = await event.get_reply_message()
        photo = None
        if replymsg and replymsg.media:
            if isinstance(replymsg.media, MessageMediaPhoto):
                photo = await event.client.download_media(message=replymsg.photo)
            elif "image" in replymsg.media.document.mime_type.split("/"):
                photo = await event.client.download_file(replymsg.media.document)
            else:
                return await edit_delete(event, INVALID_MEDIA)
        if photo:
            try:
                await event.client(
                    EditPhotoRequest(
                        event.chat_id, await event.client.upload_file(photo)
                    )
                )
                await edit_delete(event, CHAT_PP_CHANGED)
            except PhotoCropSizeSmallError:
                return await edit_delete(event, PP_TOO_SMOL)
            except ImageProcessFailedError:
                return await edit_delete(event, PP_ERROR)
            except Exception as e:
                return await edit_delete(event, f"**Ошибка : **`{str(e)}`")
            process = "updated"
    else:
        try:
            await event.client(EditPhotoRequest(event.chat_id, InputChatPhotoEmpty()))
        except Exception as e:
            return await edit_delete(event, f"**Ошибка : **`{e}`")
        process = "deleted"
        await edit_delete(event, "```успешно удалена фотография профиля группы.```")
    if BOTLOG:
        await event.client.send_message(
            BOTLOG_CHATID,
            "#GROUPPIC\n"
            f"Фотография профиля группы {process} успешно"
            f"ЧАТ: {get_display_name(await event.get_chat())}(`{event.chat_id}`)",
        )


@catub.cat_cmd(
    pattern="promote(?:\s|$)([\s\S]*)",
    command=("promote", plugin_category),
    info={
        "заголовок": "Дать права администратора человеку",
        "описание": "Предоставляет права администратора человеку в чате\
            \nПримечание. Для этого вам нужны соответствующие права.",
        "Применение": [
            "{tr}promote <userid/username/reply>",
            "{tr}promote <userid/username/reply> <custom title>",
        ],
    },
    groups_only=True,
    require_admin=True,
)
async def promote(event):
    "Продвигать человека в чате"
    new_rights = ChatAdminRights(
        add_admins=False,
        invite_users=True,
        change_info=False,
        ban_users=True,
        delete_messages=True,
        pin_messages=True,
    )
    user, rank = await get_user_from_event(event)
    if not rank:
        rank = "Admin"
    if not user:
        return
    catevent = await edit_or_reply(event, "`продвижение...`")
    try:
        await event.client(EditAdminRequest(event.chat_id, user.id, new_rights, rank))
    except BadRequestError:
        return await catevent.edit(NO_PERM)
    await catevent.edit("`Успешно продвигается! Теперь устройте вечеринку`")
    if BOTLOG:
        await event.client.send_message(
            BOTLOG_CHATID,
            f"#PROMOTE\
            \nПОЛЬЗОВАТЕЛЬ: [{user.first_name}](tg://user?id={user.id})\
            \nЧАТ: {get_display_name(await event.get_chat())} (`{event.chat_id}`)",
        )


@catub.cat_cmd(
    pattern="demote(?:\s|$)([\s\S]*)",
    command=("demote", plugin_category),
    info={
        "заголовок": "Чтобы удалить человека из списка администраторов",
        "описание": "Удаляет все права администратора для этого человека в этом чате\
            \nПримечание: для этого вам нужны соответствующие права, а также вы должны быть владельцем или администратором, который продвигал этого парня",
        "Применение": [
            "{tr}demote <userid/username/reply>",
            "{tr}demote <userid/username/reply> <custom title>",
        ],
    },
    groups_only=True,
    require_admin=True,
)
async def demote(event):
    "Чтобы понизить человека в группе"
    user, _ = await get_user_from_event(event)
    if not user:
        return
    catevent = await edit_or_reply(event, "`Понижение...`")
    newrights = ChatAdminRights(
        add_admins=None,
        invite_users=None,
        change_info=None,
        ban_users=None,
        delete_messages=None,
        pin_messages=None,
    )
    rank = "admin"
    try:
        await event.client(EditAdminRequest(event.chat_id, user.id, newrights, rank))
    except BadRequestError:
        return await catevent.edit(NO_PERM)
    await catevent.edit("`Успешно понижен в должности! Повезет в следующий раз`")
    if BOTLOG:
        await event.client.send_message(
            BOTLOG_CHATID,
            f"#DEMOTE\
            \nПОЛЬЗОВАТЕЛЬ: [{user.first_name}](tg://user?id={user.id})\
            \nЧАТ: {get_display_name(await event.get_chat())}(`{event.chat_id}`)",
        )


@catub.cat_cmd(
    pattern="ban(?:\s|$)([\s\S]*)",
    command=("ban", plugin_category),
    info={
        "заголовок": "Забанит парня в группе, где вы использовали эту команду.",
        "описание": "Он навсегда удалит его из этой группы, и он не сможет вернуться обратно\
            \nПримечание. Для этого вам нужны соответствующие права.",
        "Применение": [
            "{tr}ban <userid/username/reply>",
            "{tr}ban <userid/username/reply> <reason>",
        ],
    },
    groups_only=True,
    require_admin=True,
)
async def _ban_person(event):
    "Забанить человека в группе"
    user, reason = await get_user_from_event(event)
    if not user:
        return
    if user.id == event.client.uid:
        return await edit_delete(event, "__Вы не можете запретить себе.__")
    catevent = await edit_or_reply(event, "`Избиение вредителя!`")
    try:
        await event.client(EditBannedRequest(event.chat_id, user.id, BANNED_RIGHTS))
    except BadRequestError:
        return await catevent.edit(NO_PERM)
    reply = await event.get_reply_message()
    if reason:
        await catevent.edit(
            f"{_format.mentionuser(user.first_name ,user.id)}` забанен !!`\n**Причина : **`{reason}`"
        )
    else:
        await catevent.edit(
            f"{_format.mentionuser(user.first_name ,user.id)} ` забанен !!`"
        )
    if BOTLOG:
        if reason:
            await event.client.send_message(
                BOTLOG_CHATID,
                f"#BAN\
                \nПОЛЬЗОВАТЕЛЬ: [{user.first_name}](tg://user?id={user.id})\
                \nЧАТ: {get_display_name(await event.get_chat())}(`{event.chat_id}`)\
                \nПРИЧИНА : {reason}",
            )
        else:
            await event.client.send_message(
                BOTLOG_CHATID,
                f"#BAN\
                \nПОЛЬЗОВАТЕЛЬ: [{user.first_name}](tg://user?id={user.id})\
                \nЧАТ: {get_display_name(await event.get_chat())}(`{event.chat_id}`)",
            )
        try:
            if reply:
                await reply.forward_to(BOTLOG_CHATID)
                await reply.delete()
        except BadRequestError:
            return await catevent.edit(
                "`У меня нет прав на уничтожение сообщений! Но все равно он запрещен!`"
            )


@catub.cat_cmd(
    pattern="unban(?:\s|$)([\s\S]*)",
    command=("unban", plugin_category),
    info={
        "заголовок": "Разбанит парня в группе, где вы использовали эту команду.",
        "описание": "Удаляет учетную запись пользователя из запрещенного списка группы\
            \nПримечание. Для этого вам нужны соответствующие права.",
        "Применение": [
            "{tr}unban <userid/username/reply>",
            "{tr}unban <userid/username/reply> <reason>",
        ],
    },
    groups_only=True,
    require_admin=True,
)
async def nothanos(event):
    "Разблокировать человека"
    user, _ = await get_user_from_event(event)
    if not user:
        return
    catevent = await edit_or_reply(event, "`Разбан...`")
    try:
        await event.client(EditBannedRequest(event.chat_id, user.id, UNBAN_RIGHTS))
        await catevent.edit(
            f"{_format.mentionuser(user.first_name ,user.id)} `успешно разбанен. Предоставление еще одного шанса.`"
        )
        if BOTLOG:
            await event.client.send_message(
                BOTLOG_CHATID,
                "#UNBAN\n"
                f"ПОЛЬЗОВАТЕЛЬ: [{user.first_name}](tg://user?id={user.id})\n"
                f"Чат: {get_display_name(await event.get_chat())}(`{event.chat_id}`)",
            )
    except UserIdInvalidError:
        await catevent.edit("`О, моя логика разбана сломалась!`")
    except Exception as e:
        await catevent.edit(f"**Ошибка :**\n`{e}`")


@catub.cat_cmd(incoming=True)
async def watcher(event):
    if is_muted(event.sender_id, event.chat_id):
        try:
            await event.delete()
        except Exception as e:
            LOGS.info(str(e))


@catub.cat_cmd(
    pattern="mute(?:\s|$)([\s\S]*)",
    command=("mute", plugin_category),
    info={
        "заголовок": "Чтобы остановить отправку сообщений от этого пользователя",
        "описание": "Если он не админ, то меняет его права в группе,\
            если он админ или если попробовать в личном чате то его сообщения будут удаляться\
            \nПримечание. Для этого вам нужны соответствующие права.",
        "Применение": [
            "{tr}mute <userid/username/reply>",
            "{tr}mute <userid/username/reply> <reason>",
        ],
    },
)
async def startmute(
    event,
):  # sourcery no-metri  # sourcery skip: low-code-quality, low-code-qualitycs
    "Чтобы отключить человека в этом конкретном чате"
    if event.is_private:
        replied_user = await event.client.get_entity(event.chat_id)
        if is_muted(event.chat_id, event.chat_id):
            return await event.edit(
                "`Этот пользователь уже заглушен в этом чате  ~~lmfao sed rip~~`"
            )
        if event.chat_id == catub.uid:
            return await edit_delete(event, "`Вы не можете заглушить себя`")
        try:
            mute(event.chat_id, event.chat_id)
        except Exception as e:
            await event.edit(f"**Ошибка **\n`{e}`")
        else:
            await event.edit("`Вы успешно заглушили этого человека.\n**｀-´)⊃━☆ﾟ.*･｡ﾟ **`")
        if BOTLOG:
            await event.client.send_message(
                BOTLOG_CHATID,
                "#PM_MUTE\n"
                f"**Пользователь :** [{replied_user.first_name}](tg://user?id={event.chat_id})\n",
            )
    else:
        chat = await event.get_chat()
        admin = chat.admin_rights
        creator = chat.creator
        if not admin and not creator:
            return await edit_or_reply(
                event, "`Вы не можете заглушить человека без прав администратора niqq.` ಥ﹏ಥ  "
            )
        user, reason = await get_user_from_event(event)
        if not user:
            return
        if user.id == catub.uid:
            return await edit_or_reply(event, "`Извините, я не могу отключить`")
        if is_muted(user.id, event.chat_id):
            return await edit_or_reply(
                event, "`Этот пользователь уже заглушен в этом чате ~~lmfao sed rip~~`"
            )
        result = await event.client.get_permissions(event.chat_id, user.id)
        try:
            if result.participant.banned_rights.send_messages:
                return await edit_or_reply(
                    event,
                    "`Этот пользователь уже заглушен в этом чате ~~lmfao sed rip~~`",
                )
        except AttributeError:
            pass
        except Exception as e:
            return await edit_or_reply(event, f"**Ошибка : **`{e}`")
        try:
            await event.client(EditBannedRequest(event.chat_id, user.id, MUTE_RIGHTS))
        except UserAdminInvalidError:
            if "admin_rights" in vars(chat) and vars(chat)["admin_rights"] is not None:
                if chat.admin_rights.delete_messages is not True:
                    return await edit_or_reply(
                        event,
                        "`Вы не можете заглушить человека, если у вас нет разрешения на удаление сообщений. ಥ﹏ಥ`",
                    )
            elif "creator" not in vars(chat):
                return await edit_or_reply(
                    event, "`Вы не можете заглушить человека без прав администратора niqq.` ಥ﹏ಥ  "
                )
            mute(user.id, event.chat_id)
        except Exception as e:
            return await edit_or_reply(event, f"**Ошибка : **`{e}`")
        if reason:
            await edit_or_reply(
                event,
                f"{_format.mentionuser(user.first_name ,user.id)} `отключен в {get_display_name(await event.get_chat())}`\n"
                f"`Причина:`{reason}",
            )
        else:
            await edit_or_reply(
                event,
                f"{_format.mentionuser(user.first_name ,user.id)} `отключен в {get_display_name(await event.get_chat())}`\n",
            )
        if BOTLOG:
            await event.client.send_message(
                BOTLOG_CHATID,
                "#MUTE\n"
                f"**Пользователь :** [{user.first_name}](tg://user?id={user.id})\n"
                f"**Чат :** {get_display_name(await event.get_chat())}(`{event.chat_id}`)",
            )


@catub.cat_cmd(
    pattern="unmute(?:\s|$)([\s\S]*)",
    command=("unmute", plugin_category),
    info={
        "заголовок": "Разрешить пользователю снова отправлять сообщения",
        "описание": "Изменит права пользователя в группе, чтобы снова отправлять сообщения.\
        \nПримечание. Для этого вам нужны соответствующие права.",
        "Применение": [
            "{tr}unmute <userid/username/reply>",
            "{tr}unmute <userid/username/reply> <reason>",
        ],
    },
)
async def endmute(event):
    "Чтобы отключить человека в этом конкретном чате"
    if event.is_private:
        replied_user = await event.client.get_entity(event.chat_id)
        if not is_muted(event.chat_id, event.chat_id):
            return await event.edit(
                "`__Этот пользователь не отключен в этом чате__\n（ ^_^）o自自o（^_^ ）`"
            )
        try:
            unmute(event.chat_id, event.chat_id)
        except Exception as e:
            await event.edit(f"**Ошибка **\n`{e}`")
        else:
            await event.edit(
                "`Вы успешно включили звук этого человека\n乁( ◔ ౪◔)「    ┑(￣Д ￣)┍`"
            )
        if BOTLOG:
            await event.client.send_message(
                BOTLOG_CHATID,
                "#PM_UNMUTE\n"
                f"**Пользователь:** [{replied_user.first_name}](tg://user?id={event.chat_id})\n",
            )
    else:
        user, _ = await get_user_from_event(event)
        if not user:
            return
        try:
            if is_muted(user.id, event.chat_id):
                unmute(user.id, event.chat_id)
            else:
                result = await event.client.get_permissions(event.chat_id, user.id)
                if result.participant.banned_rights.send_messages:
                    await event.client(
                        EditBannedRequest(event.chat_id, user.id, UNBAN_RIGHTS)
                    )
        except AttributeError:
            return await edit_or_reply(
                event,
                "`Этот пользователь уже может свободно говорить в этом чате ~~lmfao sed rip~~`",
            )
        except Exception as e:
            return await edit_or_reply(event, f"**Ошибка : **`{e}`")
        await edit_or_reply(
            event,
            f"{_format.mentionuser(user.first_name ,user.id)} `розмучен в {get_display_name(await event.get_chat())}\n乁( ◔ ౪◔)「    ┑(￣Д ￣)┍`",
        )
        if BOTLOG:
            await event.client.send_message(
                BOTLOG_CHATID,
                "#UNMUTE\n"
                f"**Пользователь:** [{user.first_name}](tg://user?id={user.id})\n"
                f"**Чат :** {get_display_name(await event.get_chat())}(`{event.chat_id}`)",
            )


@catub.cat_cmd(
    pattern="kick(?:\s|$)([\s\S]*)",
    command=("kick", plugin_category),
    info={
        "заголовок": "Выкинуть человека из группы",
        "описание": "Выкинет пользователя из группы, чтобы он мог вернуться.\
        \nПримечание. Для этого вам нужны соответствующие права.",
        "Применение": [
            "{tr}kick <userid/username/reply>",
            "{tr}kick <userid/username/reply> <reason>",
        ],
    },
    groups_only=True,
    require_admin=True,
)
async def kick(event):
    "используйте это, чтобы исключить пользователя из чата"
    user, reason = await get_user_from_event(event)
    if not user:
        return
    catevent = await edit_or_reply(event, "`Кик...`")
    try:
        await event.client.kick_participant(event.chat_id, user.id)
    except Exception as e:
        return await catevent.edit(f"{NO_PERM}\n{e}")
    if reason:
        await catevent.edit(
            f"`Выгнал` [{user.first_name}](tg://user?id={user.id})`!`\nПричина: {reason}"
        )
    else:
        await catevent.edit(f"`Kicked` [{user.first_name}](tg://user?id={user.id})`!`")
    if BOTLOG:
        await event.client.send_message(
            BOTLOG_CHATID,
            "#KICK\n"
            f"ПОЛЬЗОВАТЕЛЬ: [{user.first_name}](tg://user?id={user.id})\n"
            f"ЧАТ: {get_display_name(await event.get_chat())}(`{event.chat_id}`)\n",
        )


@catub.cat_cmd(
    pattern="pin( loud|$)",
    command=("pin", plugin_category),
    info={
        "заголовок": "Для закрепления сообщений в чате",
        "описание": "ответьте на сообщение, чтобы закрепить его в чате\
        \nПримечание. Для этого вам потребуются соответствующие права, если вы хотите использовать его в группе.",
        "опции": {"Для всех": "Чтобы уведомить всех без this.it будет закреплен молча"},
        "Применение": [
            "{tr}pin <reply>",
            "{tr}pin loud <reply>",
        ],
    },
)
async def pin(event):
    "Чтобы закрепить сообщение в чате"
    to_pin = event.reply_to_msg_id
    if not to_pin:
        return await edit_delete(event, "`Ответьте на сообщение, чтобы закрепить его.`", 5)
    options = event.pattern_match.group(1)
    is_silent = bool(options)
    try:
        await event.client.pin_message(event.chat_id, to_pin, notify=is_silent)
    except BadRequestError:
        return await edit_delete(event, NO_PERM, 5)
    except Exception as e:
        return await edit_delete(event, f"`{e}`", 5)
    await edit_delete(event, "`Закреплено успешно!`", 3)
    sudo_users = _sudousers_list()
    if event.sender_id in sudo_users:
        with contextlib.suppress(BadRequestError):
            await event.delete()
    if BOTLOG and not event.is_private:
        await event.client.send_message(
            BOTLOG_CHATID,
            f"#PIN\
                \n__успешно закрепил сообщение в чате__\
                \nЧАТ: {get_display_name(await event.get_chat())}(`{event.chat_id}`)\
                \nДля всех: {is_silent}",
        )


@catub.cat_cmd(
    pattern="unpin( all|$)",
    command=("unpin", plugin_category),
    info={
        "заголовок": "Для открепления сообщений в чате",
        "описание": "ответьте на сообщение, чтобы открепить его в чате\
        \nПримечание. Для этого вам потребуются соответствующие права, если вы хотите использовать его в группе.",
        "опции": {"все": "Чтобы открепить все сообщения в чате"},
        "Применение": [
            "{tr}unpin <reply>",
            "{tr}unpin all",
        ],
    },
)
async def unpin(event):
    "Чтобы открепить сообщения в группе"
    to_unpin = event.reply_to_msg_id
    options = (event.pattern_match.group(1)).strip()
    if not to_unpin and options != "all":
        return await edit_delete(
            event,
            "__Ответьте на сообщение, чтобы открепить его или использовать __`.unpin all`__ to unpin all__",
            5,
        )
    try:
        if to_unpin and not options:
            await event.client.unpin_message(event.chat_id, to_unpin)
        elif options == "all":
            await event.client.unpin_message(event.chat_id)
        else:
            return await edit_delete(
                event, "`Ответьте на сообщение, чтобы открепить его или использовать .unpin all`", 5
            )
    except BadRequestError:
        return await edit_delete(event, NO_PERM, 5)
    except Exception as e:
        return await edit_delete(event, f"`{e}`", 5)
    await edit_delete(event, "`Откреплено успешно!`", 3)
    sudo_users = _sudousers_list()
    if event.sender_id in sudo_users:
        with contextlib.suppress(BadRequestError):
            await event.delete()
    if BOTLOG and not event.is_private:
        await event.client.send_message(
            BOTLOG_CHATID,
            f"#UNPIN\
                \n__успешно открепил(а) сообщение(я) в чате__\
                \nЧАТ: {get_display_name(await event.get_chat())}(`{event.chat_id}`)",
        )


@catub.cat_cmd(
    pattern="undlt( -u)?(?: |$)(\d*)?",
    command=("undlt", plugin_category),
    info={
        "заголовок": "Чтобы получить последние удаленные сообщения в группе",
        "описание": "Чтобы проверить последние удаленные сообщения в группе, по умолчанию отображается 5. Вы можете получить от 1 до 15 сообщений.",
        "флаги": {
            "u": "используйте этот флаг, чтобы загрузить медиа в чат, иначе оно будет отображаться как медиа."
        },
        "Применение": [
            "{tr}undlt <count>",
            "{tr}undlt -u <count>",
        ],
        "Примеры": [
            "{tr}undlt 7",
            "{tr}undlt -u 7 (это ответит на все 7 сообщений на это сообщение",
        ],
    },
    groups_only=True,
    require_admin=True,
)
async def _iundlt(event):  # sourcery no-metrics
    "Чтобы проверить последние удаленные сообщения в группе"
    catevent = await edit_or_reply(event, "`Поиск последних действий .....`")
    flag = event.pattern_match.group(1)
    if event.pattern_match.group(2) != "":
        lim = int(event.pattern_match.group(2))
        lim = min(lim, 15)
        if lim <= 0:
            lim = 1
    else:
        lim = 5
    adminlog = await event.client.get_admin_log(
        event.chat_id, limit=lim, edit=False, delete=True
    )
    deleted_msg = f"**Недавний {lim} Удаленные сообщения в этой группе :**"
    if not flag:
        for msg in adminlog:
            ruser = await event.client.get_entity(msg.old.from_id)
            _media_type = await media_type(msg.old)
            if _media_type is None:
                deleted_msg += f"\n☞ __{msg.old.message}__ **Отправлено от** {_format.mentionuser(ruser.first_name ,ruser.id)}"
            else:
                deleted_msg += f"\n☞ __{_media_type}__ **Отправлено от** {_format.mentionuser(ruser.first_name ,ruser.id)}"
        await edit_or_reply(catevent, deleted_msg)
    else:
        main_msg = await edit_or_reply(catevent, deleted_msg)
        for msg in adminlog:
            ruser = await event.client.get_entity(msg.old.from_id)
            _media_type = await media_type(msg.old)
            if _media_type is None:
                await main_msg.reply(
                    f"{msg.old.message}\n**Отправлено от** {_format.mentionuser(ruser.first_name ,ruser.id)}"
                )
            else:
                await main_msg.reply(
                    f"{msg.old.message}\n**Отправлено от** {_format.mentionuser(ruser.first_name ,ruser.id)}",
                    file=msg.old.media,
                )
