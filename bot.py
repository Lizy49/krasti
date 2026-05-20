import asyncio
import json
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, ReplyKeyboardRemove
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# === НАСТРОЙКИ (будут из переменных окружения) ===
BOT_TOKEN = os.getenv("8910571579:AAFF6-8yx0J75TxLFfRVK_0fCkn3R47ilRk")
MANAGER_ID = int(os.getenv("MANAGER_ID", "7881608441"))
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://a914851f.beget.tech/")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class OrderState(StatesGroup):
    waiting_for_comment = State()

def get_main_keyboard():
    button = KeyboardButton(text="🛍 Открыть магазин", web_app=WebAppInfo(url=WEBAPP_URL))
    return ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("👋 Добро пожаловать в KRASTI SHOP!\n\nНажмите кнопку ниже, чтобы выбрать товары. После заказа напишите адрес и пожелания.", reply_markup=get_main_keyboard())

@dp.message(lambda message: message.web_app_data is not None)
async def handle_order(message: Message, state: FSMContext):
    try:
        data = json.loads(message.web_app_data.data)
        cart = data.get("cart", [])
        total = data.get("total", 0)
        if not cart:
            await message.answer("❌ Корзина пуста.")
            return
        await state.update_data(order_cart=cart, order_total=total)
        await state.set_state(OrderState.waiting_for_comment)
        await message.answer("✅ Заказ получен!\n\n✍️ Напишите одним сообщением:\n- Адрес доставки\n- Пожелания (вкус и т.п.)\n\nПример: г. Москва, ул. Ленина 10. Вкус: Голубая малина.", reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.answer("❌ Ошибка, попробуйте снова.")

@dp.message(StateFilter(OrderState.waiting_for_comment))
async def get_comment(message: Message, state: FSMContext):
    comment = message.text.strip()
    if not comment:
        await message.answer("Напишите адрес и пожелания текстом.")
        return
    user_data = await state.get_data()
    cart = user_data.get("order_cart", [])
    total = user_data.get("order_total", 0)
    if not cart:
        await message.answer("❌ Заказ не найден. Оформите заново через магазин.")
        await state.clear()
        await message.answer("Открыть магазин", reply_markup=get_main_keyboard())
        return
    order_lines = []
    for idx, item in enumerate(cart, 1):
        name = item.get("name", "Товар")
        qty = item.get("qty", 1)
        price = item.get("price", 0)
        amount = price * qty
        order_lines.append(f"{idx}. {name}\n   {qty} шт × {price} ₽ = {amount} ₽")
    order_text = "\n".join(order_lines)
    manager_message = (f"🛒 **НОВЫЙ ЗАКАЗ (с комментарием)**\n\n📦 **Товары:**\n{order_text}\n\n💰 **Итого:** {total} ₽\n\n📝 **Комментарий:**\n{comment}\n\n👤 **Покупатель:** @{message.from_user.username or message.from_user.first_name} (id: {message.from_user.id})")
    try:
        await bot.send_message(chat_id=MANAGER_ID, text=manager_message, parse_mode="Markdown")
        await message.answer("✅ Спасибо! Заказ передан менеджеру. Он свяжется с вами.\n\nМожете продолжить покупки.", reply_markup=get_main_keyboard())
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")
        await message.answer("❌ Ошибка отправки заказа. Попробуйте позже.")
    await state.clear()

@dp.message()
async def unexpected_message(message: Message, state: FSMContext):
    if await state.get_state() != OrderState.waiting_for_comment:
        await message.answer("Чтобы сделать заказ, нажмите кнопку 'Открыть магазин'.", reply_markup=get_main_keyboard())

async def on_startup():
    webhook_url = os.getenv("RENDER_EXTERNAL_URL")
    if webhook_url:
        await bot.set_webhook(f"{webhook_url}/webhook")
        logging.info(f"Webhook set to {webhook_url}/webhook")
    else:
        logging.warning("No webhook URL, starting polling")
        asyncio.create_task(dp.start_polling(bot))

def main():
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
