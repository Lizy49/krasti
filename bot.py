import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, ReplyKeyboardRemove

# ========= ВАШИ ДАННЫЕ =========
BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
MANAGER_ID = 123456789
WEBAPP_URL = "https://Lizy49.github.io/krasti/"
# =================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class OrderState(StatesGroup):
    waiting_for_comment = State()

def get_main_keyboard():
    btn = KeyboardButton(text="🛍 Открыть магазин", web_app=WebAppInfo(url=WEBAPP_URL))
    return ReplyKeyboardMarkup(keyboard=[[btn]], resize_keyboard=True)

@dp.message(Command("start"))
async def start_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("👋 Добро пожаловать в KRASTI SHOP!\nНажмите кнопку, чтобы выбрать товары. После заказа напишите адрес и пожелания.", reply_markup=get_main_keyboard())

@dp.message(lambda m: m.web_app_data is not None)
async def order_received(message: Message, state: FSMContext):
    try:
        data = json.loads(message.web_app_data.data)
        cart = data.get("cart", [])
        total = data.get("total", 0)
        if not cart:
            await message.answer("❌ Корзина пуста.")
            return
        await state.update_data(order_cart=cart, order_total=total)
        await state.set_state(OrderState.waiting_for_comment)
        await message.answer("✅ Заказ принят!\n✍️ Напишите адрес доставки и пожелания одним сообщением.\nПример: г. Москва, ул. Ленина 10, персик со льдом.", reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        logging.error(f"Order error: {e}")
        await message.answer("❌ Ошибка, попробуйте снова.")

@dp.message(OrderState.waiting_for_comment)
async def comment_received(message: Message, state: FSMContext):
    comment = message.text.strip()
    if not comment:
        await message.answer("Напишите текст.")
        return
    data = await state.get_data()
    cart = data.get("order_cart", [])
    total = data.get("order_total", 0)
    if not cart:
        await message.answer("❌ Заказ не найден. Оформите заново.")
        await state.clear()
        await message.answer("Открыть магазин", reply_markup=get_main_keyboard())
        return
    items_text = "\n".join([f"{i+1}. {item['name']} — {item['qty']} шт × {item['price']} ₽ = {item['qty']*item['price']} ₽" for i, item in enumerate(cart)])
    manager_msg = f"🛒 НОВЫЙ ЗАКАЗ\n\n{items_text}\n\n💰 Итого: {total} ₽\n\n📝 Комментарий:\n{comment}\n\n👤 @{message.from_user.username or message.from_user.first_name}"
    try:
        await bot.send_message(MANAGER_ID, manager_msg)
        await message.answer("✅ Спасибо! Заказ отправлен менеджеру. Он свяжется с вами.", reply_markup=get_main_keyboard())
    except Exception as e:
        logging.error(f"Send error: {e}")
        await message.answer("❌ Ошибка отправки. Попробуйте позже.")
    await state.clear()

@dp.message()
async def fallback(message: Message, state: FSMContext):
    if await state.get_state() != OrderState.waiting_for_comment:
        await message.answer("Нажмите 'Открыть магазин', чтобы сделать заказ.", reply_markup=get_main_keyboard())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
