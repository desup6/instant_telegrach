import json
from telethon import TelegramClient

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    api_id = config['api_id']
    api_hash = config['api_hash']
    db_chat_id = config['db_chat_id']

saver = TelegramClient('saver', api_id, api_hash).start()


async def save_post(post_data):
    msg = await saver.send_message(db_chat_id, str(post_data))
    return msg.id


async def get_posts(ids):
    async for msg in saver.iter_messages(db_chat_id, ids=ids):
        yield msg
