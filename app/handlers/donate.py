import asyncio
import uuid
import typing

import core

from google.cloud import firestore
from functools import cached_property
from aiogram import types, dispatcher
from aiogram.utils import callback_data

from baski.telegram import receptionist


__all__ = ['register_donate_handlers']

from core import Context

_DONATION_CB_DATA = callback_data.CallbackData("donation", "amount")


def register_donate_handlers(rp: receptionist.Receptionist, ctx: core.Context, payment_token):
    donate_handler = DonateHandler(ctx, payment_token)
    rp.add_message_handler(donate_handler, commands=['donate', 'support'])
    rp.add_message_handler(donate_handler, content_types=types.ContentType.SUCCESSFUL_PAYMENT)
    rp.add_button_callback(donate_handler, _DONATION_CB_DATA.filter())
    rp.add_pre_checkout_handler(donate_handler, lambda x: x.invoice_payload.startswith('donation'))


class DonateHandler(core.BasicHandler):

    def __init__(self, ctx: Context, payment_token):
        super().__init__(ctx)
        self.payment_token = payment_token

    async def on_pre_checkout(
            self,
            pre_checkout_query: types.PreCheckoutQuery,
            state: dispatcher.FSMContext, *args,
            **kwargs
    ):
        donation_id = pre_checkout_query.invoice_payload
        pre_checkout_id = pre_checkout_query.id
        await asyncio.gather(
            pre_checkout_query.bot.answer_pre_checkout_query(pre_checkout_id, ok=True),
            self.donation_collection.document(donation_id).update(
                {'status': 'pending', 'updated_at': firestore.SERVER_TIMESTAMP}
            )
        )
        self.ctx.telemetry.add(
            user_id=pre_checkout_query.from_user.id,
            event_type=core.DONATION_PRE_CHECKOUT,
            payload={'id': donation_id, 'total_amount': pre_checkout_query.total_amount}
        )

    async def on_callback(
            self,
            callback_query: types.CallbackQuery,
            state: dispatcher.FSMContext,
            callback_data: typing.Dict[str, str] = None,
            *args, **kwargs
    ):
        amount = callback_data.get('amount', 500)
        donation = await self.start_donation(callback_query.message, amount)
        await asyncio.gather(
            callback_query.message.delete(),
            callback_query.bot.send_invoice(
                chat_id=callback_query.message.chat.id,
                photo_url='https://storage.googleapis.com/assistant-public-assets/smart_man.png',
                payload=donation['id'],
                provider_token=self.payment_token,
                currency="USD",
                prices=[types.LabeledPrice(label='Support AI Assistant', amount=amount)],
                **msg_payment.get(
                    callback_query.from_user.language_code,
                    msg_payment['en']
                )
            )
        )

    async def on_message(self, message: types.Message, state: dispatcher.FSMContext, *args, **kwargs):
        if types.ContentType.SUCCESSFUL_PAYMENT == message.content_type:
            await self.finish_donation(message)
        else:
            await message.answer(
                **msg_start_donation.get(
                    message.from_user.language_code,
                    msg_start_donation['en']
                )
            )
            self.ctx.telemetry.add_message(core.CMD_DONATE, message, message.from_user)

    async def finish_donation(self, message: types.Message):
        sp = message.successful_payment
        donation_id = sp.invoice_payload
        await asyncio.gather(
            self.donation_collection.document(donation_id).update(
                {
                    'status': 'paid',
                    'updated_at': firestore.SERVER_TIMESTAMP,
                    'total_amount': sp.total_amount,
                    "telegram_payment_charge_id": sp.telegram_payment_charge_id,
                    "provider_payment_charge_id": sp.provider_payment_charge_id
                }
            ),
            message.answer_animation(
                "https://storage.googleapis.com/assistant-public-assets/you_are_the_best.gif"
            )
        )
        self.ctx.telemetry.add(
            user_id=message.chat.id,
            event_type=core.DONATION_PAID,
            payload={'id': donation_id, 'total_amount': sp.total_amount}
        )

    async def start_donation(self, message: types.Message, amount=None):
        user_id = message.chat.id
        payment_id = '-'.join(['donation', str(uuid.uuid4())])
        payment = {
            'id': payment_id,
            'user_id': user_id,
            'type': 'donation',
            'total_amount': amount,
            'currency': 'USD',
            'updated_at': firestore.SERVER_TIMESTAMP,
            'created_at': firestore.SERVER_TIMESTAMP,
            'status': 'draft',
        }

        await self.donation_collection.document(payment_id).set(payment)
        self.ctx.telemetry.add(
            user_id=user_id,
            event_type=core.DONATION_STARTED,
            payload={'id': payment_id, 'total_amount': amount, 'currency': 'USD'}
        )
        return payment

    @cached_property
    def donation_collection(self) -> firestore.AsyncCollectionReference:
        return self.ctx.db.collection('payment')


def dontation_keyboard():
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text=text, callback_data=_DONATION_CB_DATA.new(amount=amount))
                for text, amount in [('$1 🕯️', '100'), ('5$ ☕', '500'), ('10$ 🥪', '1000'), ('$25 💳', '2500')]
            ]
        ]
    )


msg_payment = {
    "en": {
        "title": "Project support ❤️",
        "description": "Your participation is invaluable! We love you\n"
    },
    "ru": {
        "title": "Поддержка проекта ❤️",
        "description": "Ваше участие невозможно переоценить!\n"
    }
}

msg_finish_donation = {
    "en": {
        "text": "You are the best!\n"
    }
}

msg_start_donation = {
    "en": {
        "text": "🚀 Thank you so much for being willing to donate! \n"
                "🙌 Your support is invaluable to me to cover infrastructure 🖥️ and development 🛠️ cost.\n"
                "Please use the buttons below ⬇️ to continue.",
        "reply_markup": dontation_keyboard()
    },
    "ru": {
        "text": "🚀 Большое спасибо за желание сделать пожертвование!\n"
                "🙌 Ваша поддержка для меня неоценима, поскольку она покрывает расходы 🖥️ на инфраструктуру и развитие 🛠️."
                "Для продолжения используйте кнопки ⬇️ ниже».",
        "reply_markup": dontation_keyboard()
    }
}
