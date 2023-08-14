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
MAX_MESSAGE_SIZE = 4096


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
                    last_answer = answers[-1]
                    letters_to_add = len(text) - letters_written
                    text_to_add = text[letters_written:]

                    if len(last_answer.text) + letters_to_add > MAX_MESSAGE_SIZE:
                        answers.append(await message.answer(text_to_add))
                    else:
                        answers[-1] = await last_answer.edit_text(text=last_answer.text + text_to_add)
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
