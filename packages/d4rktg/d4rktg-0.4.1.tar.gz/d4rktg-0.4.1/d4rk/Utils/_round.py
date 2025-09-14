from itertools import cycle
from functools import wraps

bot_cycle = None
last_selected = None

def set_bot_cycle(bot_ids):
    global bot_cycle
    bot_cycle = cycle(bot_ids)

def round_robin():
    def decorator(func):
        @wraps(func)
        async def wrapper(client, message, *args, **kwargs):
            global last_selected, bot_cycle
            if bot_cycle is None:return
            if last_selected is None:last_selected = next(bot_cycle)
            if client.me.id == last_selected:
                result = await func(client, message, *args, **kwargs)
                last_selected = next(bot_cycle)
                return result
        return wrapper
    return decorator
