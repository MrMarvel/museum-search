import asyncio
import os
import json
from .kb import confirm_menu, start_menu, back_menu, help_menu
from .config_reader import config
from .user_session import UserSession
from .broker.rabbit_wrapper import RabbitWrapper
from aiogram import F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.filters import Command, StateFilter
from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State, default_state
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from loguru import logger
from aiogram.utils.chat_action import ChatActionMiddleware
from threading import Thread
from typing import List, Dict, Tuple
from pathlib import Path
import tempfile


user_sessions = {}

# Initialize bot
bot = Bot(token=config.bot_token.get_secret_value())
dp = Dispatcher(storage=MemoryStorage())

publisher = RabbitWrapper()
consumer = RabbitWrapper()

# Create states
class States(StatesGroup):
    input_image = State()
    process = State()


async def send_message(chat_id, msg: dict, image_path: str, state:FSMContext):
    if os.path.exists(image_path):
        os.remove(image_path)
    
    media = MediaGroupBuilder(caption=f"Топ 10 наиболее похожих изображений.")

    await bot.send_message(chat_id, text=f"Описание: {msg['caption'][0]}.")
    for hit in msg['retrieval'][0]:
        media.add_photo(FSInputFile(hit))
    await bot.send_media_group(chat_id=chat_id, media=media.build())
    message = await bot.send_message(chat_id, text=config.input_question_message, reply_markup=back_menu)
    await state.update_data({"prev_msg_id": message.message_id})


@dp.message(StateFilter(None, States.input_image), Command("start"))
async def start_handler(message: Message, state: FSMContext):
    logger.info(f'Started dialog with user {message.from_user.id}')
    await message.answer(config.start_message, reply_markup=start_menu)
    await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)


@dp.message(StateFilter(None, States.input_image), Command("help"))
async def help_handler(message: Message, state: FSMContext):
    await state.set_state(default_state)
    await message.answer(config.help_msg, reply_markup=help_menu)
    await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)


@dp.callback_query(F.data=='menu')
async def menu_handler(callback:CallbackQuery, state:FSMContext):
    await state.set_state(default_state)
    await callback.message.answer(config.start_message, reply_markup=start_menu)
    await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)


@dp.callback_query(F.data=='get_help')
async def get_help_handler(callback:CallbackQuery, state:FSMContext):
    await state.set_state(default_state)
    await callback.message.answer(config.help_msg, reply_markup=help_menu)
    await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)


@dp.callback_query(F.data=='input_image')
async def input_image(callback:CallbackQuery, state:FSMContext):
    # change state
    await state.set_state(States.input_image)
    msg = await callback.message.answer(config.input_question_message, reply_markup=back_menu)
    await state.update_data({"prev_msg_id": msg.message_id})
    await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)


@dp.message(States.input_image, F.photo)
async def input_image_handler(message: Message, state: FSMContext,):
    file = tempfile.NamedTemporaryFile(suffix='.jpg', dir='/storage', delete=False)
    await bot.download(message.photo[-1], destination=file.name)
    await state.update_data(user_image=file.name, chat_id=message.chat.id)
    # await state.update_data(user_image=os.path.join('/', *file.name.split('/')[6:]), chat_id=message.chat.id) # Для локальногго запуска
    await message.answer_photo(photo=FSInputFile(file.name), caption=config.start_search, reply_markup=confirm_menu)
    data = await state.get_data()
    prev_msg = data.get("prev_msg_id", None)
    if prev_msg:
        await bot.delete_message(chat_id=message.from_user.id, message_id=prev_msg)
        await state.update_data(prev_msg_id=None)


@dp.callback_query(F.data=='process')
async def process_handler(callback: CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    data = await state.get_data()
    # delete buttons after press
    await callback.message.edit_reply_markup()
    user_image = data.get("user_image")
    # publish message in input queue
    chat_id = data.get('chat_id')
    user_sessions[user_id] = UserSession(
        chat_id,
        callback=lambda chat_id, msg, image_path: send_message(chat_id, msg, image_path, state),
        loop=asyncio.get_event_loop()
    )
    await publisher.publish({'task': 'all', 'image_path': user_image, "user_id": user_id}, 'input')
    logger.info(f"Published question from user {user_id}: {user_image}")
    await state.set_state(States.input_image)


def start_background_loop() -> None:
    rabbit_loop = asyncio.new_event_loop()
    rabbit_loop.run_until_complete(consumer.consume(
        'bot_output',
        publish_queue_name=None,
        pipeline=None,
        callback_map=user_sessions
    ))
    rabbit_loop.run_forever()


async def main():
    dp.message.middleware(ChatActionMiddleware())
    await dp.start_polling(bot)


if __name__ == '__main__':
    thread = Thread(target=start_background_loop, daemon=True)
    thread.start()
    asyncio.run(main())