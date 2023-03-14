import asyncio
from aiogram import types


class TypingBlock(object):

    def __init__(self, chat: types.Chat):
        self.chat = chat
        self.typing_task = None

    async def __aenter__(self):
        await self.chat.do("typing")

        async def typing_cycle(chat):
            try:
                await chat.do("typing")
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                pass

        self.typing_task = asyncio.get_event_loop().create_task(typing_cycle(self.chat))

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.typing_task and isinstance(self.typing_task, asyncio.Task):
            self.typing_task.cancel()
