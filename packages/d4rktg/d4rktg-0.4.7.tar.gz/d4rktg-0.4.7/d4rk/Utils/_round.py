from itertools import cycle
from functools import wraps
from pyrogram.types import Message

last_selected_per_chat = {}

def round_robin():
    def decorator(func):
        @wraps(func)
        async def wrapper(client, message: Message, *args, **kwargs):
            chat_id = message.chat.id

            # Private chats: all bots respond
            if message.chat.type.name.lower() == "private":
                return await func(client, message, *args, **kwargs)

            # If first message in chat, set current bot as last_selected
            if chat_id not in last_selected_per_chat:
                last_selected_per_chat[chat_id] = client.me.id

            # Only the last_selected bot responds
            if client.me.id == last_selected_per_chat[chat_id]:
                result = await func(client, message, *args, **kwargs)

                # rotate: pick the next bot (you'll need a list of bot IDs per chat)
                bots_in_chat = list({client.me.id})  # replace with actual bot list
                idx = bots_in_chat.index(client.me.id)
                last_selected_per_chat[chat_id] = bots_in_chat[(idx + 1) % len(bots_in_chat)]
                return result

        return wrapper
    return decorator