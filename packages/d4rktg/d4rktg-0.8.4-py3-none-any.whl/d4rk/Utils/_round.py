from functools import wraps
from pyrogram import filters
from pyrogram.types import Message
import asyncio
import re
from d4rk.Logs import setup_logger

logger = setup_logger(__name__)

last_index_per_chat = {}
bot_order_per_chat = {}
responded_messages = {}
chat_locks = {}

def round_robin():
    def decorator(func):
        @wraps(func)
        async def wrapper(client, message, *args, **kwargs):
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
                chat_locks[chat_id] = asyncio.Lock()

            # Add new bot if not in the chat
            if client.me.id not in bot_order_per_chat[chat_id]:
                bot_order_per_chat[chat_id].append(client.me.id)

            async with chat_locks[chat_id]:
                # Skip if message already responded
                if msg_id in responded_messages[chat_id]:
                    return

                # Decide which bot should respond
                current_index = last_index_per_chat[chat_id]
                selected_bot_id = bot_order_per_chat[chat_id][current_index]

                if client.me.id == selected_bot_id:
                    result = await func(client, message, *args, **kwargs)
                    # Mark message as responded
                    responded_messages[chat_id].add(msg_id)
                    # Rotate for next message
                    last_index_per_chat[chat_id] = (current_index + 1) % len(bot_order_per_chat[chat_id])
                    return result

        return wrapper
    return decorator
