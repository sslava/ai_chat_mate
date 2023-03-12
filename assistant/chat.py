import logging
import random

from aiogram import types
from aiogram.dispatcher import FSMContext

from .telegram import dp
from .open_ai_client import get_joke, get_assistance


JOKE_PROBABILITY = 0.1


# https://platform.openai.com/docs/usage-policies/platform-policy
@dp.message_handler(commands=["start"])
async def welcome(message: types.Message):
    await message.answer(
        "Hey!\n"
        "I am ChatGPT based, a conversational bot created by @galilei. "
        "My purpose is to assist and engage in conversations with users on a variety of topics."
        "I can help answer questions, provide information, and have discussions with you.\n\n"
        "Here is some examples, try one of them:\n"
        "What's the capital of France?\n"
        "Translate 'Hello, how are you?' to French.\n"
        "Generate a short story about a detective solving a murder case."
    )


@dp.message_handler()
async def answer(message: types.Message, state: FSMContext):
    handler = get_handler(message)

    data = await state.get_data()
    history = data.get('history') or []
    history = history + [{"role": "user", "content": message.text}]
    if handler is None:
        await state.set_data({"history": history[-10:]})
        return
    try:
        ai_message = await handler(
            user_id=message.from_user.id,
            history=history
        )
        await message.answer(ai_message)
        history = history + [{"role": "assistant", "content": ai_message}]

    except Exception as e:
        logging.error(f"Exception while process {message.text} from {message.from_user.id}: {e}")

    await state.set_data({"history": history[-10:]})


def get_handler(message: types.Message):
    if message.chat.type == 'private':
        return get_assistance

    if message.chat.type == 'group' and 'ai_chat_mate_bot' in message.text:
        return get_assistance

    if message.chat.type == 'group' and random.random() < JOKE_PROBABILITY:
        return get_joke

    return None
