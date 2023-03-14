import asyncio
import random

from aiogram import types
from aiogram.dispatcher import FSMContext

from .telegram import dp
from .open_ai_client import get_joke, get_assistance
from .i_can_break import sorry_if_exception
from .cmd_credits import maybe_send_credits
from .typing_block import TypingBlock

JOKE_PROBABILITY = 0.05
NUM_LAST_MESSAGES = 10


@dp.message_handler()
@sorry_if_exception()
@dp.async_task()
async def answer(message: types.Message, state: FSMContext, *args, **kwargs):
    handler = get_handler(message)

    data = await state.get_data()
    history = data.get('history') or []
    history = history + [{"role": "user", "content": message.text}]
    if handler is None:
        await state.set_data({"history": history[-10:]})
        return

    async with TypingBlock(message.chat):
        _, ai_message = await asyncio.gather(
            maybe_send_credits(message),
            handler(user_id=message.from_user.id, history=history)
        )

    await message.answer(ai_message)
    history = history + [{"role": "assistant", "content": ai_message}]

    await state.set_data({"history": history[-NUM_LAST_MESSAGES:]})


def get_handler(message: types.Message):
    if message.chat.type == 'private':
        return get_assistance

    if message.chat.type == 'group' and 'ai_chat_mate_bot' in message.text:
        return get_assistance

    if message.chat.type == 'group' and random.random() < JOKE_PROBABILITY:
        return get_joke

    return None
