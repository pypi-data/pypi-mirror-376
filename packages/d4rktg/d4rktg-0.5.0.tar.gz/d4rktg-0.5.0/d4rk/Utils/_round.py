from functools import wraps
from pyrogram.types import Message

# Track last bot index per chat
last_index_per_chat = {}
# Track bot order per chat
bot_order_per_chat = {}
# Track messages already responded to: chat_id -> set of message_ids
responded_messages = {}

def round_robin():
    def decorator(func):
        @wraps(func)
        async def wrapper(client, message: Message, *args, **kwargs):
            chat_id = message.chat.id
            msg_id = message.id

            # Private chats: all bots respond
            if message.chat.type.name.lower() == "private":
                return await func(client, message, *args, **kwargs)

            # Initialize tracking for this chat
            if chat_id not in bot_order_per_chat:
                bot_order_per_chat[chat_id] = [client.me.id]
                last_index_per_chat[chat_id] = 0
                responded_messages[chat_id] = set()

            # Skip if message already responded by any bot
            if msg_id in responded_messages[chat_id]:
                return

            # Add new bots if not in the chat
            if client.me.id not in bot_order_per_chat[chat_id]:
                bot_order_per_chat[chat_id].append(client.me.id)

            current_index = last_index_per_chat[chat_id]
            selected_bot_id = bot_order_per_chat[chat_id][current_index]

            # Only selected bot responds
            if client.me.id == selected_bot_id:
                result = await func(client, message, *args, **kwargs)
                # Mark message as responded
                responded_messages[chat_id].add(msg_id)
                # Rotate index
                last_index_per_chat[chat_id] = (current_index + 1) % len(bot_order_per_chat[chat_id])
                return result

        return wrapper
    return decorator
