from itertools import cycle
from functools import wraps
from pyrogram.types import Message

last_selected = None
bot_order = []

def round_robin():
    def decorator(func):
        @wraps(func)
        async def wrapper(client, message: Message, *args, **kwargs):
            global last_selected, bot_order

            # Private chats: all bots respond
            if message.chat.type.name.lower() == "private":
                return await func(client, message, *args, **kwargs)

            # If this chat is new, start order dynamically
            chat_id = message.chat.id
            if chat_id not in bot_order:
                bot_order.append(client.me.id)
                last_selected = client.me.id

            # Only the "current" bot responds
            if client.me.id == last_selected:
                result = await func(client, message, *args, **kwargs)

                # Rotate for next message
                alive_bots = [b for b in bot_order if b is not None]  # optionally skip dead bots
                idx = alive_bots.index(last_selected)
                last_selected = alive_bots[(idx + 1) % len(alive_bots)]
                return result
        return wrapper
    return decorator
