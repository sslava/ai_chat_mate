from dataclasses import dataclass, field
from baski.telegram import storage
from baski.primitives import datetime


@dataclass()
class TelegramUser(storage.TelegramUser):
    last_credits: datetime.datetime = field(default=datetime.datetime.fromtimestamp(0))


