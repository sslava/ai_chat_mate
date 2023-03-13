import asyncio
import typing
import logging
import inspect

from aiogram import types as aiogram_types


def sorry_if_exception():

    def wrapper(fn: typing.Callable):
        _name = fn_name(fn)
        assert inspect.iscoroutinefunction(fn), "Only async functions supported"

        async def inner(message: aiogram_types.Message, *args, **kwargs):
            try:
                await fn(message, *args, **kwargs)
            except asyncio.CancelledError:
                logging.warning(f"Coroutine {_name} was cancelled. Live is different", _name)
            except (SystemExit, KeyboardInterrupt, GeneratorExit):
                raise
            except Exception as e:
                logging.error(f'{e} while call {_name}')

                if isinstance(message, aiogram_types.Message):
                    await message.reply(**I_AM_SORRY)
                if isinstance(message, aiogram_types.CallbackQuery):
                    await message.message.reply(**I_AM_SORRY)
        return inner

    return wrapper


I_AM_SORRY = {
    "text": "I'm sorry, something is broken inside. Unfortunately, "
            "I can't complete your request. You may try one more time."
}


def fn_name(fn) -> str:
    """
    Returns callable dotted name including module
    :param fn:
    :return:
    """
    parts = [fn.__module__]
    if hasattr(fn, '__qualname__'):
        parts.append(fn.__qualname__)
    return '.'.join(parts)
