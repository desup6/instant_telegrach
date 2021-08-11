import datetime
import time
import json
import asyncio

from re import findall
from telethon import TelegramClient, events, Button
from telethon.errors.rpcerrorlist import MessageNotModifiedError, MessageDeleteForbiddenError
from telethon.tl.types import DocumentAttributeFilename, MessageMediaPhoto, MessageMediaDocument, Photo, PhotoSize, \
    PhotoPathSize, PhotoSizeProgressive, Document, DocumentAttributeImageSize, DocumentAttributeAudio, \
    DocumentAttributeSticker, InputStickerSetID, DocumentAttributeVideo, DocumentAttributeAnimated, InputStickerSetEmpty  # всё это нужно для файлов, которые хранятся в виде строки-объекта
from hashlib import sha3_512
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from string import ascii_lowercase, digits
from random import choices, randint

from captcha import generate_captcha
from database import get_posts, save_post

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    api_id = config['api_id']
    api_hash = config['api_hash']
    bot_token = config['bot_token']
    salt = config['salt']
    saving_interval = config['saving_interval']
    main_text = config['main_text']
    rules_text = config['rules_text']
    boards = config['boards']
    about_url = config['about_url']
    board_buttons = [Button.inline(boards[board_code], board_code) for board_code in boards.keys()]
    main_buttons = [board_buttons[x:x+2] for x in range(0, len(board_buttons), 2)] + [[Button.url('❔ О борде', about_url), Button.inline('📖 Правила', 'rules')]]

service_buttons = [[Button.inline('⬅', 'prev'), None, Button.inline('➡', 'next')],
                   [Button.inline('↪ На главную', 'main')]]

with open('threads.json', 'r', encoding='utf-8') as f:
    threads = json.load(f)
    for board in boards:
        if board not in threads.keys():
            threads[board] = {'posts': 0, 'threads': []}

with open('userstates.json', 'r', encoding='utf-8') as f:
    userstates = json.load(f)


class savingThread(Thread):
    def run(self):
        while True:
            time.sleep(saving_interval)
            with open('threads.json', 'w') as f:
                json.dump(threads, f, indent=4)
            with open('userstates.json', 'w') as f:
                json.dump(userstates, f, indent=4)


saving_thread = savingThread()
saving_thread.start()

bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)


async def get_user_hash(event):
    try:
        id = event.query.peer
    except AttributeError:
        id = event.peer_id.user_id
    user = await bot.get_entity(id)
    identifier = str(user.id) + str(user.access_hash) + salt
    user_hash = sha3_512(identifier.encode()).hexdigest()
    return user_hash


async def go_to_board(peer, id, board, page):
    page_threads = threads[board]['threads'][(page - 1) * 10:page * 10]
    buttons = [[Button.inline(f'№{thread["num"]}: {thread["op_post_shortened"]}', thread["num"] + board)] for thread in page_threads] + service_buttons
    buttons[-2][1] = Button.inline(f'🔄', board)

    try:
        await bot.edit_message(peer, id, f'{boards[board]} - всего постов: {threads[board]["posts"]}\nCтраница {page}',
                               buttons=buttons, file=f'images/{board}_banner.png')
    except MessageNotModifiedError:
        pass


async def send_new_posts(thread, last_index, peer, id, hash):
    board = findall(r'\D+', thread)[0]
    thread_num = findall(r'\d+', thread)[0]
    ids = [t for t in threads[board]['threads'] if t['num'] == thread_num][0]['ids'][last_index:]
    new_last_index = last_index
    async for post in get_posts(ids):
        post_dict = eval(post.text)
        num = post_dict['num']
        file = eval(post_dict['file'])
        reply_num = post_dict['reply_to']
        reply_id = None
        if reply_num:
            reply_id = userstates[hash][1][reply_num]
        msg = await bot.send_message(peer, '№' + num + '\n' + post_dict['text'], file=file, reply_to=reply_id)
        userstates[hash][1][num] = msg.id
        new_last_index += 1

    await bot.send_message(peer, 'ᅠ', buttons=[[Button.inline(f'🔄 Обновить', id + 'update' + str(new_last_index))],
                                               [Button.inline(f'❌ Закрыть тред', 'del' + id)]])


@bot.on(events.NewMessage(pattern='/start', func=lambda e: e.is_private))
async def handler(event):
    hash = await get_user_hash(event)
    userstates[hash] = ['main', None]
    await bot.send_message(event.peer_id, main_text, buttons=main_buttons, file='images/main.png')


@bot.on(events.CallbackQuery(pattern='rules', func=lambda e: e.is_private))
async def callback(event):
    hash = await get_user_hash(event)
    userstates[hash] = ['rules', None]
    await bot.edit_message(event.query.peer, event.message_id, rules_text, buttons=[[Button.inline('↪ На главную', 'main')]], file='images/rules.png')


@bot.on(events.CallbackQuery(pattern=lambda s: s.decode() in boards, func=lambda e: e.is_private))
async def callback(event):
    board = event.data.decode()
    hash = await get_user_hash(event)
    userstates[hash] = [board, 1]

    await go_to_board(event.query.peer, event.message_id, board, 1)
    await event.answer()


@bot.on(events.CallbackQuery(pattern='prev|next', func=lambda e: e.is_private))
async def callback(event):
    hash = await get_user_hash(event)
    board = userstates[hash][0]
    page = userstates[hash][1]

    if event.data.decode() == 'prev':
        page -= 1
    elif event.data.decode() == 'next':
        page += 1

    page_threads = threads[board]['threads'][(page - 1) * 10:page * 10]
    if page == 0 or not page_threads:
        await event.answer()
        return

    userstates[hash][1] = page
    await go_to_board(event.query.peer, event.message_id, board, page)
    await event.answer()


@bot.on(events.CallbackQuery(pattern='main', func=lambda e: e.is_private))
async def callback(event):
    hash = await get_user_hash(event)
    userstates[hash] = ['main', None]
    await bot.edit_message(event.query.peer, event.message_id, main_text, buttons=main_buttons, file='images/main.png')


@bot.on(events.CallbackQuery(pattern='new_', func=lambda e: e.is_private))
async def callback(event):
    hash = await get_user_hash(event)
    msg = await event.get_message()
    reply = await msg.get_reply_message()
    text = reply.message
    file = reply.media

    if event.data.decode() == 'new_thread':
        board = userstates[hash][0]
        threads[board]['posts'] += 1
        num = str(threads[board]['posts'])

        post_data = {
            'num': str(num),
            'text': datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S") + '\n' + text[:2000],
            'file': str(file),
            'reply_to': None
        }

        id = await save_post(post_data)
        threads[board]['threads'].insert(0, {'ids': [id], 'num': num, 'op_post_shortened': text[:50]})

    elif event.data.decode() == 'new_post':
        thread = userstates[hash][0]
        thread_num = findall(r'\d+', thread)[0]
        board = findall(r'\D+', thread)[0]
        threads[board]['posts'] += 1
        num = str(threads[board]['posts'])

        post_reply = await reply.get_reply_message()
        reply_num = None
        if post_reply:
            reply_num = post_reply.message.split('\n')[0][1:]

        post_data = {
            'num': str(num),
            'text': datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S") + '\n' + text[:2000],
            'file': str(file),
            'reply_to': reply_num
        }

        id = await save_post(post_data)
        thread_index = [threads[board]['threads'].index(thread) for thread in threads[board]['threads'] if
                        thread['num'] == thread_num][0]
        thread_dict = threads[board]['threads'].pop(thread_index)
        thread_dict['ids'].append(id)
        threads[board]['threads'].insert(0, thread_dict)

    await msg.delete()
    await reply.delete()


@bot.on(events.CallbackQuery(pattern='cancel', func=lambda e: e.is_private))
async def callback(event):
    msg = await event.get_message()
    reply = await msg.get_reply_message()
    await msg.delete()
    await reply.delete()


@bot.on(events.CallbackQuery(pattern=lambda s: findall(r'\d+', s.decode()) and findall(r'\D+', s.decode()) and findall(r'\D+', s.decode())[0] in boards, func=lambda e: e.is_private))
async def callback(event):
    thread = event.data.decode()
    thread_num = findall(r'\d+', thread)[0]
    board = findall(r'\D+', thread)[0]
    hash = await get_user_hash(event)
    userstates[hash] = [thread, {}]

    try:
        await bot.edit_message(event.query.peer, event.message_id, f'/{board}/ - тред №{thread_num}', buttons=None)
    except MessageNotModifiedError:
        pass
    await send_new_posts(thread, 0, event.query.peer, str(event.message_id), hash)


# @bot.on(events.Album)?? надо бы добавить поддержку альбомов
@bot.on(events.NewMessage(func=lambda e: e.is_private))
async def handler(event):
    hash = await get_user_hash(event)
    userstate = userstates[hash][0]
    if userstate in boards:
        if not event.message.message or not event.message.media:
            await event.reply('Нельзя создать тред без текста/медиа', buttons=[[Button.inline('Отмена', 'cancel')]], file='images/refuse.png')
        else:
            await event.reply('Вы создаёте новый тред', buttons=[[Button.inline('Капча', 'captcha_thread')],
                                                                 [Button.inline('Отмена', 'cancel')]], file='images/posting.png')
    elif userstate[0].isdigit():
        await event.reply('Вы создаёте новый пост', buttons=[[Button.inline('Капча', 'captcha_post')],
                                                             [Button.inline('Отмена', 'cancel')]], file='images/posting.png')
    else:
        await event.delete()


@bot.on(events.CallbackQuery(pattern='captcha_', func=lambda e: e.is_private))
async def handler(event):
    res = ''.join(choices(ascii_lowercase + digits, k=5))
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        img = await loop.run_in_executor(pool, generate_captcha, res)

    if event.data.decode() == 'captcha_thread':
        buttons = [Button.inline(''.join(choices(ascii_lowercase + digits, k=5)), 'captcha_thread') for x in range(5)]
        buttons.insert(randint(0, 6), Button.inline(res, 'new_thread'))
    else:
        buttons = [Button.inline(''.join(choices(ascii_lowercase + digits, k=5)), 'captcha_post') for x in range(5)]
        buttons.insert(randint(0, 6), Button.inline(res, 'new_post'))

    await bot.edit_message(event.query.peer, event.message_id, 'Выберите правильный вариант',
                           buttons=[buttons[:3], buttons[3:], [Button.inline('Отмена', 'cancel')]], file=img)


@bot.on(events.CallbackQuery(pattern='.+update.+', func=lambda e: e.is_private))
async def callback(event):
    hash = await get_user_hash(event)
    thread = userstates[hash][0]
    data = event.data.decode().split('update')
    await bot.delete_messages(event.query.peer, event.message_id)
    await send_new_posts(thread, int(data[1]), event.query.peer, data[0], hash)


@bot.on(events.CallbackQuery(pattern='del', func=lambda e: e.is_private))
async def callback(event):
    hash = await get_user_hash(event)
    thread = userstates[hash][0]

    st_id = int(event.data.decode()[3:])
    board = findall(r'\D+', thread)[0]

    ids = [x for x in range(event.message_id, st_id, -1)]
    try:
        await bot.delete_messages(event.query.peer, ids)
    except MessageDeleteForbiddenError:
        pass

    await go_to_board(event.query.peer, st_id, board, 1)
    userstates[hash] = [board, 1]


bot.run_until_disconnected()
