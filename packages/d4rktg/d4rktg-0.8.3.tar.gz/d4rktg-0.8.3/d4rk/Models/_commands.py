import re
import requests
import asyncio

from typing import Union
from functools import wraps
from pyrogram import Client, filters
from pyrogram.types import Message

from d4rk.Logs import setup_logger
from d4rk.Utils import clear_terminal

logger = setup_logger(__name__)


command_registry = []


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

def get_priority(description: str) -> int:
    desc_lower = description.lower()
    if "(owner only)" in desc_lower:
        return 4
    elif "(sudo only)" in desc_lower:
        return 3
    elif "(admin only)" in desc_lower:
        return 2
    else:
        return 1

def reorder_command_registry():
    global command_registry
    command_registry.sort(key=lambda cmd: get_priority(cmd["description"]))

def get_commands():
    return command_registry

def command(command: Union[str, list], description: str,Custom_filter=None):
    def decorator(func):
        command_registry.append({
            "command": command,
            "description": description,
            "handler": func
        })
        logger.info(f"Registered command: {command} - {description}")
        if Custom_filter:
            filter = filters.command(command) & Custom_filter
        else:
            filter = filters.command(command)
        @Client.on_message(filter)
        @round_robin()
        @wraps(func)
        async def wrapper(client, message):
            return await func(client, message)
        reorder_command_registry()
        clear_terminal()
        return wrapper
    return decorator

class CommandAI:
    def __init__(self):
        self.api_key = "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"
        self.api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
        self.headers = {"Authorization": "Bearer " + self.api_key}

    def __post(self,payload):   
        response = requests.post(self.api_url, headers=self.headers, json=payload)
        if response.status_code != 200:
            print(f"❌ Error {response.status_code}: {response.text}")
            return None
        return response.json()
    
    def extract_username(self, query: str):
        match = re.search(r'@[\w\d_]+', query)
        return match.group(0) if match else None

    def get_command(self,user_query):
        labels = [entry["description"] for entry in command_registry]
        response = self.__post(
            payload={
                "inputs": user_query,
                "parameters": {"candidate_labels": labels},
            }
        )
        print(response)
        if response is None:return None
        best_label = response["labels"][0]
        if best_label is None:
            logger.error("No matching command found for the user query.")
            return None
        for entry in command_registry:
            if entry["description"] == best_label:
                return entry["command"] if isinstance(entry["command"], str) else entry["command"][0]
        return None

find_command = CommandAI()
