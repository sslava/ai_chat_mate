from aiogram.dispatcher import FSMContext

from aiogram import types
from .telegram import dp
from .i_can_break import sorry_if_exception


@dp.message_handler(commands=["clear"])
@sorry_if_exception()
async def clear_history(message: types.Message, state: FSMContext, *args, **kwargs):
    data = await state.get_data()
    data['history'] = []
    await state.set_data(data)

    answer = msg_clear.get(
        message.from_user.language_code,
        msg_clear['en']
    )
    await message.answer(**answer)


msg_clear = {
    "en": {
        "text": "My context is clean and fresh. Please keep going.",
    },
    "ru": {
        "text": "Моя память чиста и пуста. Пожалуйста, продолжайте.",
    }
}
