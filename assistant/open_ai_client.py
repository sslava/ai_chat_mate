import logging

import openai
import os
import asyncio
from openai.openai_object import OpenAIObject
openai.api_key = os.getenv("OPENAI_KEY")


# loyal friend who likes to give advices
as_assistant = """
You are the  helpful, creative, joyful, friendly, trustworthy assistant
""".strip()

cgi = {
    "model": "gpt-3.5-turbo",
    "n": 1,
    "temperature": 1.1
}

as_comedian = """
You are a creative, friendly American comedian. Tell the joke as an answer. Don't mention language model
"""


def get_assistance(user_id, history):
    return create_message(as_assistant, user_id, history)


def get_joke(user_id, history):
    return create_message(as_comedian, user_id, history)


async def create_message(promt, user_id, history):
    history = history or []
    messages = [{"role": "system", "content": promt}] + history
    for i in range(0, 5):
        try:
            response: OpenAIObject = openai.ChatCompletion.create(messages=messages, user=str(user_id), **cgi)
            return response['choices'][0]['message']['content']
        except openai.error.APIError as e:
            logging.warning(f"Get exception from OpenAI: {e}")
            await asyncio.sleep(i**2)
