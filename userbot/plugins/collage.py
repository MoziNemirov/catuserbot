# collage plugin for catuserbot by @sandy1709

# Copyright (C) 2020 Alfiananda P.A
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.import os

import os

from userbot import Convert, catub

from ..core.managers import edit_delete, edit_or_reply
from ..helpers import _catutils, meme_type, reply_id

plugin_category = "utils"


@catub.cat_cmd(
    pattern="collage(?:\s|$)([\s\S]*)",
    command=("collage", plugin_category),
    info={
        "заголовок": "Для создания коллажа из неподвижных изображений, извлеченных из видео/gif.",
        "описание": "Показывает изображение сетки изображений, извлеченных из видео/gif. вы можете настроить размер сетки, указав целое число от 1 до 9 для cmd, по умолчанию это 3",
        "Применение": "{tr}collage <1-9>",
    },
)
async def collage(event):
    "Для создания коллажа из неподвижных изображений, извлеченных из видео/gif."
    catinput = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    catid = await reply_id(event)
    if not (reply and (reply.media)):
        return await edit_delete(event, "`Ответ на медиафайл..`")
    mediacheck = await meme_type(reply)
    if mediacheck not in [
        "Round Video",
        "Gif",
        "Video Sticker",
        "Animated Sticker",
        "Video",
    ]:
        return await edit_delete(
            event, "`Тип носителя ответного сообщения не поддерживается.`"
        )
    if catinput:
        if not catinput.isdigit():
            return await edit_delete(event, "`Вы вводите неверно, проверьте справку`")

        catinput = int(catinput)
        if not 0 < catinput < 10:
            await edit_or_reply(
                event,
                "__Почему при большой сетке вы не можете видеть изображения, используйте размер сетки от 1 до 9\nВсе равно измените значение на максимальное 9__",
            )
            catinput = 9
    else:
        catinput = 3
    await edit_or_reply(event, "```Создание коллажа может занять несколько минут...... 😁```")
    if mediacheck in ["Round Video", "Gif", "Video Sticker", "Video"]:
        if not os.path.isdir("./temp/"):
            os.mkdir("./temp/")
        catsticker = await reply.download_media(file="./temp/")
        collagefile = catsticker
    else:
        collage_file = await Convert.to_gif(
            event, reply, file="collage.mp4", noedits=True
        )
        collagefile = collage_file[1]
    if not collagefile:
        await edit_or_reply(
            event, "**Ошибка:-** __Не удалось обработать отвеченный носитель__"
        )
    endfile = "./temp/collage.png"
    catcmd = f"vcsi -g {catinput}x{catinput} '{collagefile}' -o {endfile}"
    stdout, stderr = (await _catutils.runcmd(catcmd))[:2]
    if not os.path.exists(endfile) and os.path.exists(collagefile):
        os.remove(collagefile)
        return await edit_delete(
            event, "`Носитель не поддерживается или попробуйте с меньшим размером сетки`"
        )
    await event.client.send_file(
        event.chat_id,
        endfile,
        reply_to=catid,
    )
    await event.delete()
    for files in (collagefile, endfile):
        if files and os.path.exists(files):
            os.remove(files)
