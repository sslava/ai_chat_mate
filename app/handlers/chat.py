import functools
import io
import random
import openai
import asyncio
import tempfile
import typing
from copy import deepcopy

import langdetect

from aiogram import types, dispatcher
from aiogram.utils.exceptions import MessageNotModified, RetryAfter, TelegramAPIError
from google.cloud import texttospeech as tts
from langdetect import LangDetectException

from baski.concurrent import as_async
from baski.telegram import chat, storage, monitoring
from baski.primitives import datetime
from baski.pattern import retry

import core
from .credits import CreditsHandler

__all__ = ['ChatHandler']

CHAT_HISTORY_LENGTH = 7
CREDITS_COOLDOWN = datetime.timedelta(days=5)
CREDITS_PROBABILITY = 0.05
MAX_MESSAGE_SIZE = 4096


class ChatHandler(core.BasicHandler):

    async def on_message(
            self,
            message: types.Message,
            state: dispatcher.FSMContext,
            *args, **kwargs
    ):
        if message.voice:
            message.text = await self.text_from_voice(message)
        await chat.aiogram_retry(message.chat.do, "typing")
        self.ctx.telemetry.add_message(monitoring.MESSAGE_IN, message, message.from_user)

        user: storage.TelegramUser = kwargs.get('user')
        async with state.proxy() as proxy:
            history = chat.ChatHistory(proxy)
            history.from_user(message)
            try:
                answers = await self.answer_to_text(user, message, history)
            except openai.error.InvalidRequestError as e:
                await chat.aiogram_retry(
                    message.answer,
                    f"Large request are not supported yet. "
                    f"Please try again with a shorter message.\n\n The /donate command is available to support large requests."
                )
                self.ctx.telemetry.add_message(core.LARGE_MESSAGE, message, message.from_user)
            for answer in answers:
                history.from_ai(answer)
                self.ctx.telemetry.add_message(monitoring.MESSAGE_OUT, answer, message.from_user)
        await self.maybe_show_credits(message, user)

    async def answer_to_text(self, user, message, history):
        answers: typing.List[types.Message] = []
        last_answer_began = 0
        letters_written = 0
        async for text in self.ctx.openai.continue_chat(
                user_id=user.id,
                history=history.last(CHAT_HISTORY_LENGTH, fmt="openai"),
                message=message.text):
            try:
                if not answers:
                    if text:
                        answers.append(await chat.aiogram_retry(message.answer, text))
                        letters_written = len(text)
                    continue

                if len(text) - last_answer_began > MAX_MESSAGE_SIZE:
                    if message.voice:
                        await self.send_voice(message, answers[-1].text)
                    last_answer_began = letters_written
                    answers.append(await chat.aiogram_retry(message.answer, text[letters_written:]))
                else:
                    if answers[-1].text != text[last_answer_began:]:
                        answers[-1] = await chat.aiogram_retry(answers[-1].edit_text, text=text[last_answer_began:])
                letters_written = len(text)
                await chat.aiogram_retry(message.chat.do, "typing")
            except MessageNotModified as e:
                pass
            except RetryAfter:
                await asyncio.sleep(1)
        if message.voice:
            await self.send_voice(message, answers[-1].text)
        return answers

    async def maybe_show_credits(
            self,
            message: types.Message,
            user: core.TelegramUser,
            *args, **kwargs
    ):
        if datetime.now() - datetime.as_local(user.last_credits) < CREDITS_COOLDOWN:
            return
        if random.random() > CREDITS_PROBABILITY:
            return
        credits_message = await CreditsHandler.send_to(message, user, self.ctx.users)
        self.ctx.telemetry.add_message(core.SHOW_CREDITS, credits_message, message.from_user)

    async def send_voice(self, message, text):
        try:
            language = langdetect.detect(text)
        except LangDetectException:
            return
        voice = self.get_voice(language)
        if not voice:
            await chat.aiogram_retry(message.answer, f"Sorry, I don't know how to speak {language} yet")
            return
        synthesis_input = tts.SynthesisInput(text=text)
        voice = tts.VoiceSelectionParams(
            language_code=language, name=voice
        )
        audio_config = tts.AudioConfig(
            audio_encoding=tts.AudioEncoding.OGG_OPUS, speaking_rate=1.0
        )
        await message.chat.do('record_voice')
        response = await as_async(
            self.ctx.tts_client.synthesize_speech,
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        await chat.aiogram_retry(message.answer_voice, response.audio_content)

    async def text_from_voice(self, message):
        with tempfile.TemporaryDirectory() as tempdir:
            placeholder = await chat.aiogram_retry(message.reply, "🎙 Transcribing voice message...")
            await message.chat.do("typing")
            buffer = await retry(
                message.voice.download,
                exceptions=(TelegramAPIError,),
                destination_dir=tempdir
            )
            buffer.flush()
            with io.FileIO(buffer.name, 'rb') as read_buffer:
                text = await self.ctx.openai.transcribe(read_buffer)
                await chat.aiogram_retry(placeholder.edit_text, f"🎙 Transcription is: \"{text}\"")
                return text

    def get_voice(self, language):
        possible_voices = [v for v in self.available_voices if v.startswith(language)]
        if not possible_voices:
            return None
        wavenet_voices = [v for v in possible_voices if 'Wavenet' in v]
        if wavenet_voices:
            return random.choice(wavenet_voices)
        return random.choice(possible_voices)

    @functools.cached_property
    def available_voices(self) -> typing.List[str]:
        return [v.name for v in self.ctx.tts_client.list_voices().voices if v.ssml_gender == tts.SsmlVoiceGender.MALE]
