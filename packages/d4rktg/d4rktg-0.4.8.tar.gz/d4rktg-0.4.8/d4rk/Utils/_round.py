from functools import wraps
from pyrogram.types import Message

# Track last bot per chat
last_selected_per_chat = {}
# Track all bot IDs dynamically
active_bot_ids = []

def round_robin():
    def decorator(func):
        @wraps(func)
        async def wrapper(client, message: Message):
            chat_id = message.chat.id

            # Private chats: all bots respond
            if message.chat.type.name.lower() == "private":
                return await func(client, message)

            # Add bot ID to active list dynamically
            if client.me.id not in active_bot_ids:
                active_bot_ids.append(client.me.id)

            # Initialize last_selected for this chat
            if chat_id not in last_selected_per_chat:
                last_selected_per_chat[chat_id] = client.me.id

            # Only the selected bot responds
            if client.me.id == last_selected_per_chat[chat_id]:
                result = await func(client, message)

                # Rotate to the next bot
                idx = active_bot_ids.index(client.me.id)
                last_selected_per_chat[chat_id] = active_bot_ids[(idx + 1) % len(active_bot_ids)]
                return result

        return wrapper
    return decorator
