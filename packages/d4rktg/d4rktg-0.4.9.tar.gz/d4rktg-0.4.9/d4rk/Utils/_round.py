from functools import wraps
from pyrogram.types import Message

# Track last bot index per chat
last_index_per_chat = {}
# Track all bot IDs dynamically
active_bot_ids = []

def round_robin():
    def decorator(func):
        @wraps(func)
        async def wrapper(client, message: Message, *args, **kwargs):
            chat_id = message.chat.id

            # Private chats: all bots respond
            if message.chat.type.name.lower() == "private":
                return await func(client, message, *args, **kwargs)

            # Add bot ID to active list dynamically
            if client.me.id not in active_bot_ids:
                active_bot_ids.append(client.me.id)

            # Initialize last_index for this chat
            if chat_id not in last_index_per_chat:
                last_index_per_chat[chat_id] = 0

            current_index = last_index_per_chat[chat_id]
            selected_bot_id = active_bot_ids[current_index]

            # Only the selected bot responds
            if client.me.id == selected_bot_id:
                result = await func(client, message, *args, **kwargs)

                # Rotate to next bot index
                last_index_per_chat[chat_id] = (current_index + 1) % len(active_bot_ids)
                return result

        return wrapper
    return decorator