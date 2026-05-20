import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, ReplyKeyboardRemove

# =========== ВАШИ ДАННЫЕ (измените) ===========
BOT_TOKEN = "8910571579:AAFF6-8yx0J75TxLFfRVK_0fCkn3R47ilRk"
MANAGER_ID = 7881608441         # Telegram ID менеджера
WEBAPP_URL = "http://a914851f.beget.tech/" 
# =============================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class OrderState(StatesGroup):
    waiting_for_comment = State()

def get_main_keyboard():
    btn = KeyboardButton(text="🛍 Открыть магазин", web_app=WebAppInfo(url=WEBAPP_URL))
    return ReplyKeyboardMarkup(keyboard=[[btn]], resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("👋 Добро пожаловать в KRASTI SHOP!\n\nНажмите кнопку, чтобы выбрать товары. После заказа напишите адрес и пожелания.", reply_markup=get_main_keyboard())

@dp.message(lambda m: m.web_app_data is not None)
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
        await message.answer("✅ Заказ получен!\n\n✍️ Напишите одним сообщением:\n- Адрес доставки\n- Пожелания (например, вкус)\n\nПример: г. Москва, ул. Ленина 10, кв 5. Вкус: Голубая малина.", reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        logging.error(f"Order error: {e}")
        await message.answer("❌ Ошибка, попробуйте снова.")

@dp.message(StateFilter(OrderState.waiting_for_comment))
async def get_comment(message: Message, state: FSMContext):
    comment = message.text.strip()
    if not comment:
        await message.answer("Напишите адрес и пожелания текстом.")
        return
    data = await state.get_data()
    cart = data.get("order_cart", [])
    total = data.get("order_total", 0)
    if not cart:
        await message.answer("❌ Заказ не найден. Оформите заново через магазин.")
        await state.clear()
        await message.answer("Открыть магазин", reply_markup=get_main_keyboard())
        return
    order_lines = []
    for i, item in enumerate(cart, 1):
        name = item.get("name", "Товар")
        qty = item.get("qty", 1)
        price = item.get("price", 0)
        amount = price * qty
        order_lines.append(f"{i}. {name} — {qty} шт × {price} ₽ = {amount} ₽")
    order_text = "\n".join(order_lines)
    manager_msg = f"🛒 **НОВЫЙ ЗАКАЗ (с комментарием)**\n\n📦 **Товары:**\n{order_text}\n\n💰 **Итого:** {total} ₽\n\n📝 **Комментарий:**\n{comment}\n\n👤 **Покупатель:** @{message.from_user.username or message.from_user.first_name} (id: {message.from_user.id})"
    try:
        await bot.send_message(chat_id=MANAGER_ID, text=manager_msg, parse_mode="Markdown")
        await message.answer("✅ Спасибо! Заказ передан менеджеру. Он свяжется с вами.\n\nМожете продолжить покупки.", reply_markup=get_main_keyboard())
    except Exception as e:
        logging.error(f"Send error: {e}")
        await message.answer("❌ Не удалось отправить заказ. Попробуйте позже.")
    await state.clear()

@dp.message()
async def fallback(message: Message, state: FSMContext):
    if await state.get_state() != OrderState.waiting_for_comment:
        await message.answer("Чтобы сделать заказ, нажмите кнопку 'Открыть магазин'.", reply_markup=get_main_keyboard())

async def main():
    print("Бот запущен и ожидает заказы...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
