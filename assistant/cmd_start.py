from aiogram import types

from .telegram import dp
from .cmd_credits import send_credits
from .i_can_break import sorry_if_exception


# https://platform.openai.com/docs/usage-policies/platform-policy
@dp.message_handler(commands=["start"])
@sorry_if_exception()
async def welcome_user(message: types.Message, *args, **kwargs):
    await send_credits(message)

    greeting_text = msg_greeting.get(
        msg_greeting[message.from_user.language_code],
        msg_greeting['en']
    )

    await message.answer(greeting_text)

msg_greeting = {
    "en":
        "Hey!\n"
        "I am ChatGPT based, a conversational bot. "
        "My purpose is to assist and engage in conversations with users on a variety of topics."
        "I can help answer questions, provide information, and have discussions with you.\n\n"
        "Here is some examples, try one of them:\n"
        "What's the capital of France?\n"
        "Translate 'Hello, how are you?' to French.\n"
        "Generate a short story about a detective solving a murder case.",
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
