from aiogram import types
from baski.primitives import datetime
from baski.telegram import storage
import core

__all__ = ['CreditsHandler']


class CreditsHandler(core.BasicHandler):

    async def on_message(
            self,
            message: types.Message,
            user: core.TelegramUser,
            *args, **kwargs
    ):
        await self.send_to(message, user, self.ctx.users)
        self.ctx.telemetry.add_message(core.CMD_CREDITS, message, message.from_user)

    @classmethod
    async def send_to(cls, message: types.Message, user: core.TelegramUser, users: storage.UsersStorage):
        answer = msg_credits.get(
            message.from_user.language_code,
            msg_credits['en']
        )
        user.last_credits = datetime.now()
        users.set(user)
        return await message.answer(**answer)


FEEDBACK_URL = "https://3qugszanpzk.typeform.com/to/ifCEiciG"
GITHUB_URL = "https://github.com/vgalilei/ai_chat_mate"


msg_credits = {
    "en": {
        "parse_mode": "MarkdownV2",
        "text": "This bot is developed 🛠️ by @galilei\. "
                "You are more than welcome to reach out with a suggestion or complain\."
                "\n\nYour conversation is safe \- "
                "bot never stores any of your messages without your explicit permission\. "
                "The code is open\. Feel free to review the GitHub page\. "
                "\n\nIf this bot is useful for you it will be useful for your friends\. "
                "\n\n*We need your help to spread the word about this bot*\. Feel free to share it with your friends and colleagues"
                "\n\nTo support the project you can /donate to the author\, or just leave a feedback\."
                ,
        "reply_markup": types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton("🔗 Source code", url=GITHUB_URL),
                    types.InlineKeyboardButton("💬 Leave feedback", url=FEEDBACK_URL)
                ]
            ])
    },
    "ru": {
        "parse_mode": "MarkdownV2",
        "text": "«Этот бот разработан @galilei\. "
                "Вы всегда можете обратиться с предложением или жалобой\. "
                "\n\nВаш разговор в безопасности \— "
                "бот никогда не сохраняет ваши сообщения без вашего явного разрешения\. "
                "Код открыт\. Посетите страницу проекта на GitHub"
                "\n\nЕсли этот бот полезен для вас\, он будет полезен и для ваших друзей\. "
                "Пожалуйста\, не стесняйтесь поделиться им c друзьями и коллегами",
        "reply_markup": types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton("🔗 Исходный код", url=GITHUB_URL),
                    types.InlineKeyboardButton("💬 Поделиться идеей", url=FEEDBACK_URL)
                ]
            ])
    }
}
