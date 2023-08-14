import random
import asyncio
from aiogram import types, dispatcher
from aiogram.utils.exceptions import MessageNotModified, RetryAfter

from baski.telegram import chat, storage, monitoring
from baski.primitives import datetime

import core
from .credits import CreditsHandler

__all__ = ['ChatHandler']

CHAT_HISTORY_LENGTH = 7
CREDITS_COOLDOWN = datetime.timedelta(days=5)
CREDITS_PROBABILITY = 0.01
MAX_MESSAGE_SIZE = 64


class ChatHandler(core.BasicHandler):

    async def on_message(
            self,
            message: types.Message,
            state: dispatcher.FSMContext,
            *args, **kwargs
    ):
        self.ctx.telemetry.add_message(monitoring.MESSAGE_IN, message)
        user: storage.TelegramUser = kwargs.get('user')
        async with state.proxy() as proxy:
            history = chat.ChatHistory(proxy)
            history.from_user(message)

            answers = []
            await message.chat.do("typing")
            last_answer_began = 0
            letters_written = 0
            async for text in self.ctx.openai.continue_chat(
                    user_id=user.id,
                    history=history.last(CHAT_HISTORY_LENGTH, fmt="openai"),
                    message=message.text):
                try:
                    if not answers:
                        answers.append(await message.answer(text))
                        letters_written = len(text)
                        continue

                    if len(text) - last_answer_began > MAX_MESSAGE_SIZE:
                        last_answer_began = letters_written
                        answers.append(await message.answer(text[letters_written:]))
                    else:
                        answers[-1] = await answers[-1].edit_text(text=text[last_answer_began:])
                    letters_written = len(text)
                    await message.chat.do("typing")
                except MessageNotModified as e:
                    pass
                except RetryAfter:
                    await asyncio.sleep(1)

            for answer in answers:
                history.from_ai(answer)
                self.ctx.telemetry.add_message(monitoring.MESSAGE_OUT, answer)
        await self.maybe_show_credits(message, user)

    async def maybe_show_credits(
            self,
            message: types.Message,
            user: core.TelegramUser,
            *args, **kwargs
    ):
        if datetime.now() - datetime.as_local(user.last_credits) < CREDITS_COOLDOWN:
            return
        if random.random() > CREDITS_PROBABILITY:
            return
        await CreditsHandler.send_to(message, user, self.ctx.users)
