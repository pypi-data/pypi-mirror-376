from itertools import cycle
from functools import wraps
from pyrogram import Message

bot_cycle = None
last_selected = None

def set_bot_cycle(bot_ids):
    global bot_cycle
    bot_cycle = cycle(bot_ids)

def round_robin():
    def decorator(func):
        @wraps(func)
        async def wrapper(client, message:Message, *args, **kwargs):
            global last_selected, bot_cycle
            if message.chat.type.name.lower() == "private":
                return await func(client, message, *args, **kwargs)
            if bot_cycle is None:return
            if last_selected is None:last_selected = next(bot_cycle)
            if client.me.id == last_selected:
                result = await func(client, message, *args, **kwargs)
                last_selected = next(bot_cycle)
                return result
        return wrapper
    return decorator
