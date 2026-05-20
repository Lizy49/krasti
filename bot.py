import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.types import ReplyKeyboardRemove

# ===== НАСТРОЙКИ (замените на свои) =====
BOT_TOKEN = "8910571579:AAFF6-8yx0J75TxLFfRVK_0fCkn3R47ilRk"
MANAGER_ID = 7881608441 # Telegram ID менеджера
WEBAPP_URL = "http://a914851f.beget.tech/"  # Ссылка на ваш магазин (WebApp)
# =========================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Состояния FSM: ожидаем комментарий после заказа
class OrderState(StatesGroup):
    waiting_for_comment = State()

# Клавиатура с кнопкой открытия магазина
def get_main_keyboard():
    button = KeyboardButton(
        text="🛍 Открыть магазин",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )
    keyboard = ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True)
    return keyboard

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    # Сбрасываем состояние (на всякий случай)
    await state.clear()
    await message.answer(
        "👋 Добро пожаловать в KRASTI SHOP!\n\n"
        "Нажмите кнопку ниже, чтобы выбрать товары. После оформления заказа напишите ваш адрес и пожелания.",
        reply_markup=get_main_keyboard()
    )

# Обработка данных из WebApp (заказ)
@dp.message(lambda message: message.web_app_data is not None)
async def handle_order(message: Message, state: FSMContext):
    try:
        data = json.loads(message.web_app_data.data)
        cart = data.get("cart", [])
        total = data.get("total", 0)

        if not cart:
            await message.answer("❌ Корзина пуста. Выберите товары в магазине.")
            return

        # Сохраняем заказ в FSM
        await state.update_data(order_cart=cart, order_total=total)
        await state.set_state(OrderState.waiting_for_comment)

        # Спрашиваем адрес и пожелания
        await message.answer(
            "✅ Заказ получен!\n\n"
            "✍️ Пожалуйста, напишите одним сообщением:\n"
            "- Ваш адрес доставки\n"
            "- Пожелания к заказу (например, желаемый вкус, цвет, дополнительные опции)\n\n"
            "Пример: г. Москва, ул. Ленина 10, кв 5. Персик со льдом, без накипи.\n\n"
            "Отправьте текст, и я передам его менеджеру.",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        logging.error(f"Ошибка при обработке заказа: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте ещё раз.")

# Обработка комментария (адрес + пожелания) от пользователя
@dp.message(StateFilter(OrderState.waiting_for_comment))
async def get_comment(message: Message, state: FSMContext):
    comment = message.text.strip()
    if not comment:
        await message.answer("Пожалуйста, напишите адрес и пожелания текстом.")
        return

    # Получаем сохранённый заказ
    user_data = await state.get_data()
    cart = user_data.get("order_cart", [])
    total = user_data.get("order_total", 0)

    if not cart:
        await message.answer("❌ Заказ не найден. Пожалуйста, оформите заказ заново через магазин.")
        await state.clear()
        await message.answer("Нажмите кнопку 'Открыть магазин'", reply_markup=get_main_keyboard())
        return

    # Формируем сообщение для менеджера
    order_lines = []
    for idx, item in enumerate(cart, 1):
        name = item.get("name", "Товар")
        qty = item.get("qty", 1)
        price = item.get("price", 0)
        amount = price * qty
        order_lines.append(f"{idx}. {name}\n   {qty} шт × {price} ₽ = {amount} ₽")
    order_text = "\n".join(order_lines)

    manager_message = (
        f"🛒 **НОВЫЙ ЗАКАЗ (с комментарием)**\n\n"
        f"📦 **Товары:**\n{order_text}\n\n"
        f"💰 **Итого:** {total} ₽\n\n"
        f"📝 **Комментарий покупателя:**\n{comment}\n\n"
        f"👤 **Покупатель:** @{message.from_user.username or message.from_user.first_name} (id: {message.from_user.id})"
    )

    # Отправляем менеджеру
    try:
        await bot.send_message(chat_id=MANAGER_ID, text=manager_message, parse_mode="Markdown")
        await message.answer(
            "✅ Спасибо! Ваш заказ и комментарий переданы менеджеру.\n"
            "Он свяжется с вами в ближайшее время.\n\n"
            "Вы можете продолжить покупки, нажав кнопку 'Открыть магазин'.",
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        logging.error(f"Ошибка отправки менеджеру: {e}")
        await message.answer("❌ Не удалось отправить заказ менеджеру. Попробуйте позже.")
        await message.answer("Открыть магазин", reply_markup=get_main_keyboard())

    # Завершаем состояние
    await state.clear()

# Если пользователь пишет что-то вне состояния (не заказ, не комментарий)
@dp.message()
async def unexpected_message(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == OrderState.waiting_for_comment:
        # Уже обработано в get_comment, сюда не попадёт
        pass
    else:
        await message.answer(
            "Чтобы сделать заказ, нажмите кнопку 'Открыть магазин'.",
            reply_markup=get_main_keyboard()
        )

# Запуск
async def main():
    print("Бот запущен и ожидает заказы...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())