import argparse
import typing
from functools import cached_property, lru_cache
from google.cloud import pubsub
from aiogram.dispatcher import storage as aiogram_storage

from baski.env import get_env
from baski.server import aiogram_server
from baski.telegram import storage, filters, handlers, middleware, monitoring
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
            pubsub=self.pubsub,
            openai=self.openai_clinet,
            users=self.users,
            telemetry=monitoring.MessageTelemetry(self.pubsub, self.args['project_id'])
        )

    @cached_property
    def pubsub(self):
        return pubsub.PublisherClient()

    def add_arguments(self, parser: argparse.ArgumentParser):
        super().add_arguments(parser)
        parser.add_argument('--openai-token', help='OpenAI API token', default=str(get_env('OPENAI_TOKEN', '')))
        parser.add_argument('--payment-token', help="Telegram payment token", default=str(get_env("PAYMENT_TOKEN", "")))

    def register_handlers(self):
        app_handlers.register_donate_handlers(self.receptionist, self.context, self.args['payment_token'])

        self.receptionist.add_error_handler(handlers.SaySorryHandler())
        self.receptionist.add_message_handler(app_handlers.ClearHandler(self.context), commands=['clear'])
        self.receptionist.add_message_handler(app_handlers.StartHandler(self.context), commands=['start'])
        self.receptionist.add_message_handler(app_handlers.CreditsHandler(self.context), commands=['credits'])
        self.receptionist.add_message_handler(app_handlers.ChatHandler(self.context), chat_type='private')

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
            middleware.UnprocessedMiddleware(self.context.telemetry)
        ]


if __name__ == '__main__':
    ChatMateBot().run()
