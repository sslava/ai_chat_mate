from dataclasses import dataclass
from google.cloud import firestore, pubsub
from baski.telegram import storage, monitoring
from .openai_client import OpenAiClient


__all__ = ['Context']


@dataclass
class Context:
    db: firestore.AsyncClient
    pubsub: pubsub.PublisherClient
    openai: OpenAiClient
    users: storage.UsersStorage
    telemetry: monitoring.MessageTelemetry
