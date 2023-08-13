import argparse
import typing
from functools import cached_property, lru_cache
from aiogram.dispatcher import storage as aiogram_storage

from baski.env import get_env
from baski.server import aiogram_server
from baski.telegram import storage, filters, handlers, middleware
import handlers as app_handlers, core


class ChatMateBot(aiogram_server.TelegramServer):

    @cached_property
    def users(self):
        return storage.UsersStorage(self.db.collection('telegram_users'), core.TelegramUser)

    @cached_property
    def fsm_storage(self) -> aiogram_storage.BaseStorage:
        return storage.FirebaseStorage(self.db)

    @cached_property
    def openai_clinet(self):
        return core.OpenAiClient(self.args['openai_token'])

    @cached_property
    def context(self):
        return core.Context(
            db=self.db,
            openai=self.openai_clinet,
            users=self.users,
        )

    def add_arguments(self, parser: argparse.ArgumentParser):
        super().add_arguments(parser)
        parser.add_argument('--openai-token', help='OpenAI API token', default=str(get_env('OPENAI_TOKEN', '')))

    def register_handlers(self):
        self.receptionist.add_error_handler(handlers.SaySorryHandler())
        self.receptionist.add_message_handler(app_handlers.ClearHandler(), commands=['clear'])
        self.receptionist.add_message_handler(app_handlers.StartHandler(self.context), commands=['start'])
        self.receptionist.add_message_handler(app_handlers.CreditsHandler(self.context), commands=['credits'])
        self.receptionist.add_message_handler(app_handlers.ChatHandler(self.context))

    def web_routes(self) -> typing.List:
        return []

    @lru_cache()
    def filters(self) -> typing.List:
        filters.User.setup(self.users)
        return [
            filters.User
        ]

    def middlewares(self) -> typing.List:
        return [
            middleware.UnprocessedMiddleware()
        ]


if __name__ == '__main__':
    ChatMateBot().run()
