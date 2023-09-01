from aiogram import types, dispatcher

from .credits import CreditsHandler
import core

__all__ = ['StartHandler']


CHAT_HISTORY_LENGTH = 7


class StartHandler(core.BasicHandler):

    async def on_message(
            self,
            message: types.Message,
            *args,
            user: core.TelegramUser,
            **kwargs
    ):
        self.ctx.telemetry.add_message(core.CMD_START, message, message.from_user)
        greeting_text = msg_greeting.get(message.from_user.language_code, msg_greeting['en'])
        await message.answer(greeting_text)
        await CreditsHandler.send_to(message, user, self.ctx.users)


msg_greeting = {
    "en":
        "Hey there! 👋\n"
        "I am ChatGPT based, a conversational bot. "
        "My purpose is to assist and engage in conversations with users on a variety of topics."
        "I can help answer questions, provide information, and have discussions with you.\n\n"
        "👋 Here is some examples, try one of them:\n"
        "- What's the capital of France?\n"
        "- Translate 'Hello, how are you?' to French.\n"
        "- Generate a short story about a detective solving a murder case.",
    "ru":
        "Здравствуйте!\n"
        "Я - ChatGPT, бот для разговоров. "
        "Моя задача - помогать и участвовать в разговорах с пользователями на различные темы. "
        "Я могу помочь ответить на вопросы, рассказать необходимую информацию и провести общение с вами.\n\n"
        "Вот несколько примеров, попробуйте один из них:\n"
        "Какая столица Франции?\n"
        "Переведи фразу 'Привет, как дела?' на французский.\n"
        "Напиши короткую историю о детективе, который решает дело об убийстве.\n"

}
