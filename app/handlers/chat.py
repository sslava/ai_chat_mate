import random
from aiogram import types, dispatcher

from baski.telegram import chat, storage
from baski.primitives import datetime

import core
from .credits import CreditsHandler


__all__ = ['ChatHandler']


CHAT_HISTORY_LENGTH = 7
CREDITS_COOLDOWN = datetime.timedelta(days=5)
CREDITS_PROBABILITY = 0.01


class ChatHandler(core.BasicHandler):

    async def on_message(
            self,
            message: types.Message,
            state: dispatcher.FSMContext,
            *args, **kwargs
    ):
        user: storage.TelegramUser = kwargs.get('user')
        async with state.proxy() as proxy:
            history = chat.ChatHistory(proxy)
            history.from_user(message)

            answer = await message.answer("...")
            await message.chat.do("typing")
            async for text in self.ctx.openai.continue_chat(
                    user_id=user.id,
                    history=history.last(CHAT_HISTORY_LENGTH, fmt="openai"),
                    message=message.text):
                answer = await answer.edit_text(text=text)
                await message.chat.do("typing")

            history.from_ai(answer)
        await self.maybe_show_credits(message, user)

    async def maybe_show_credits(
            self,
            message: types.Message,
            user: core.TelegramUser,
            *args, **kwargs
    ):
        if datetime.now() - user.last_credits < CREDITS_COOLDOWN:
            return
        if random.random() > CREDITS_PROBABILITY:
            return
        await CreditsHandler.send_to(message, user, self.ctx.users)
