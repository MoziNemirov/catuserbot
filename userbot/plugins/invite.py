from telethon import functions

from userbot import catub

from ..core.managers import edit_delete, edit_or_reply

plugin_category = "utils"


@catub.cat_cmd(
    pattern="invite ([\s\S]*)",
    command=("invite", plugin_category),
    info={
        "заголовок": "Добавьте данного пользователя/пользователей в группу, в которой вы использовали команду.",
        "описание": "Добавляет только упомянутого человека или бота, а не всех участников",
        "Применение": "{tr}invite <username(s)/userid(s)>",
        "Примеры": "{tr}invite @combot @MissRose_bot",
    },
)
async def _(event):
    "Чтобы пригласить пользователя в чат."
    to_add_users = event.pattern_match.group(1)
    if not event.is_channel and event.is_group:
        # https://lonamiwebs.github.io/Telethon/methods/messages/add_chat_user.html
        for user_id in to_add_users.split(" "):
            try:
                await event.client(
                    functions.messages.AddChatUserRequest(
                        chat_id=event.chat_id, user_id=user_id, fwd_limit=1000000
                    )
                )
            except Exception as e:
                return await edit_delete(event, f"`{str(e)}`", 5)
    else:
        # https://lonamiwebs.github.io/Telethon/methods/channels/invite_to_channel.html
        for user_id in to_add_users.split(" "):
            try:
                await event.client(
                    functions.channels.InviteToChannelRequest(
                        channel=event.chat_id, users=[user_id]
                    )
                )
            except Exception as e:
                return await edit_delete(event, f"`{e}`", 5)

    await edit_or_reply(event, f"`{to_add_users} приглашен успешно `")
