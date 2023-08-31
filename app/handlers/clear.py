from aiogram import types, dispatcher
import core
from baski.telegram import chat


__all__ = ['ClearHandler']


CHAT_HISTORY_LENGTH = 7


class ClearHandler(core.BasicHandler):

    async def on_message(self, message: types.Message, state: dispatcher.FSMContext, *args, **kwargs):
        self.ctx.telemetry.add_message(core.CMD_CLEAR, message, message.from_user)
        async with state.proxy() as proxy:
            chat.ChatHistory(proxy).clear()
        answer = msg_clear.get(
            message.from_user.language_code,
            msg_clear['en']
        )
        await message.answer(**answer)


msg_clear = {
    "en": {
        "text": "My context is clean. Please keep going.",
    },
    "ru": {
        "text": "Моя память чиста. Пожалуйста, продолжайте.",
    }
}
