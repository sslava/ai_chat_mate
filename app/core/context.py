from dataclasses import dataclass
from google.cloud import firestore
from baski.telegram import storage
from .openai_client import OpenAiClient


__all__ = ['Context']


@dataclass
class Context:
    db: firestore.AsyncClient
    openai: OpenAiClient
    users: storage.UsersStorage
