"""
Roast Lab — Aiogram 3.x Telegram Bot Companion
Handles coffee catalog, drip packs, pre-order to arrival, and 1-click repeat orders.
"""

import asyncio
import os
import sys
import json
from datetime import datetime, time
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8217851677:AAHN34TMuC1P4e6SppuazFN8BIiLHa_RyIc")
OWNER_ID = int(os.environ.get("TELEGRAM_OWNER_ID", "1387913438"))
OWNER_USERNAME = os.environ.get("TELEGRAM_OWNER_USERNAME", "@Idrisov_prod")

router = Router()

class PreorderState(StatesGroup):
    waiting_for_drink = State()
    waiting_for_time = State()
    waiting_for_name = State()

def is_cafe_open() -> bool:
    now = datetime.now().time()
    return time(8, 0) <= now <= time(22, 0)

def get_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="☕ Зерно (250г / 1кг)", callback_data="cat_beans")],
        [InlineKeyboardButton(text="💧 Дрип-пакеты (боксы 10 шт)", callback_data="cat_drips")],
        [InlineKeyboardButton(text="⏳ Предзаказ к приходу (Takeaway)", callback_data="start_preorder")],
        [InlineKeyboardButton(text="🔁 Повторить прошлый заказ (1-Click)", callback_data="reorder_last")],
        [InlineKeyboardButton(text="📍 Локация кофейни & Часы", callback_data="cafe_info")]
    ])

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        "☕ <b>Добро пожаловать в спешелти-кофейню Roast Lab!</b>\n\n"
        "Мы обжариваем свежие микролоты с высокогорных плантаций Эфиопии, Кении, Колумбии и Коста-Рики.\n\n"
        "🕒 <b>Часы работы:</b> ежедневно с 08:00 до 22:00\n"
        "📍 <b>Адрес:</b> Москва, ул. Покровка, 12\n\n"
        "Выберите действие в меню:"
    )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_menu())

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("☕ <b>Главное меню Roast Lab:</b>", parse_mode="HTML", reply_markup=get_main_menu())
    await call.answer()

# --- Beans Showcase ---
@router.callback_query(F.data == "cat_beans")
async def cb_beans_catalog(call: CallbackQuery):
    beans = database.get_all_beans()
    kb = []
    for b in beans:
        btn_text = f"{b['name'][:22]}… — {b['price_250g']} ₽"
        kb.append([InlineKeyboardButton(text=btn_text, callback_data=f"bean_{b['slug']}")])
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")])
    
    await call.message.edit_text(
        "☕ <b>Свежеобжаренное зерно в пачках 250г:</b>\nВыберите лот для описания и заказа:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await call.answer()

@router.callback_query(F.data.startswith("bean_"))
async def cb_bean_detail(call: CallbackQuery):
    slug = call.data.replace("bean_", "")
    bean = database.get_bean_by_slug(slug)
    if not bean:
        await call.answer("Лот не найден", show_alert=True)
        return
        
    text = (
        f"☕ <b>{bean['name']}</b>\n\n"
        f"🌍 <b>Происхождение:</b> {bean['origin']} ({bean['altitude']})\n"
        f"💧 <b>Обработка:</b> {bean['process']} | Обжарка: {bean['roast_level']}\n"
        f"🍓 <b>Дескрипторы вкуса:</b> {bean['descriptors']}\n\n"
        f"📊 <b>Профиль чашки:</b>\n"
        f"• Кислотность: {'●' * bean['acidity']}{'○' * (10 - bean['acidity'])}\n"
        f"• Сладость: {'●' * bean['sweetness']}{'○' * (10 - bean['sweetness'])}\n"
        f"• Тело: {'●' * bean['body']}{'○' * (10 - bean['body'])}\n\n"
        f"💰 <b>Цена:</b> {bean['price_250g']} ₽ за 250г / {bean['price_1kg']} ₽ за 1кг"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🛍 Купить 250г ({bean['price_250g']} ₽)", callback_data=f"buy_bean_{bean['slug']}_250g")],
        [InlineKeyboardButton(text=f"📦 Купить 1кг ({bean['price_1kg']} ₽)", callback_data=f"buy_bean_{bean['slug']}_1kg")],
        [InlineKeyboardButton(text="⬅️ К списку сортов", callback_data="cat_beans")]
    ])
    
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data.startswith("buy_bean_"))
async def cb_buy_bean(call: CallbackQuery):
    parts = call.data.split("_")
    slug = parts[2]
    variant = parts[3]
    bean = database.get_bean_by_slug(slug)
    
    price = bean['price_250g'] if variant == "250g" else bean['price_1kg']
    user = call.from_user
    username = f"@{user.username}" if user.username else f"ID {user.id}"
    
    order_data = {
        "user_identifier": str(user.id),
        "client_name": user.full_name,
        "phone": username,
        "order_type": "delivery",
        "items_json": json.dumps([{"title": f"{bean['name']} ({variant})", "quantity": 1, "price_rub": price}], ensure_ascii=False),
        "total_amount_rub": price,
        "notes": f"Заказ зерна из Telegram-бота ({variant})"
    }
    order_id = database.create_order(order_data)
    
    await call.message.edit_text(
        f"🎉 <b>Заказ #{order_id} оформлен!</b>\n\n"
        f"Позиция: <b>{bean['name']} ({variant})</b>\n"
        f"Сумма: <b>{price} ₽</b>\n\n"
        f"Бариста Roast Lab ({OWNER_USERNAME}) упакует зерно и свяжется с вами для доставки!",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
        ])
    )
    await call.answer()

# --- Drips Showcase ---
@router.callback_query(F.data == "cat_drips")
async def cb_drips_catalog(call: CallbackQuery):
    drips = database.get_all_drip_packs()
    kb = []
    for d in drips:
        kb.append([InlineKeyboardButton(text=f"{d['title']} — {d['price_rub']} ₽", callback_data=f"buy_drip_{d['id']}")])
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")])
    
    await call.message.edit_text(
        "💧 <b>Дрип-пакеты (10 шт в боксе):</b>\nНатуральный спешелти кофе прямо в вашей чашке:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await call.answer()

@router.callback_query(F.data.startswith("buy_drip_"))
async def cb_buy_drip(call: CallbackQuery):
    drip_id = int(call.data.replace("buy_drip_", ""))
    drips = database.get_all_drip_packs()
    drip = next((d for d in drips if d["id"] == drip_id), None)
    
    user = call.from_user
    username = f"@{user.username}" if user.username else f"ID {user.id}"
    
    order_data = {
        "user_identifier": str(user.id),
        "client_name": user.full_name,
        "phone": username,
        "order_type": "delivery",
        "items_json": json.dumps([{"title": drip["title"], "quantity": 1, "price_rub": drip["price_rub"]}], ensure_ascii=False),
        "total_amount_rub": drip["price_rub"],
        "notes": "Заказ дрип-пакетов из бота"
    }
    order_id = database.create_order(order_data)
    
    await call.message.edit_text(
        f"🎉 <b>Заказ #{order_id} принят!</b>\n\n"
        f"Вы заказали: <b>{drip['title']}</b>\n"
        f"К оплате: <b>{drip['price_rub']} ₽</b>\n\n"
        f"Дрип-боксы отправляются в течение суток курьерской службой или доступны для самовывоза.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
        ])
    )
    await call.answer()

# --- Pre-order to arrival (Takeaway with time picker) ---
@router.callback_query(F.data == "start_preorder")
async def cb_preorder_start(call: CallbackQuery, state: FSMContext):
    warning = ""
    if not is_cafe_open():
        warning = "\n\n⚠️ <i>Кофейня сейчас закрыта (часы: 08:00 - 22:00). Ваш заказ будет готов к открытию в 08:00!</i>"
        
    await state.set_state(PreorderState.waiting_for_drink)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="☕ Флэт Уайт (350 ₽)", callback_data="pre_drink_Flat White_350")],
        [InlineKeyboardButton(text="🥛 Капучино 300мл (320 ₽)", callback_data="pre_drink_Cappuccino_320")],
        [InlineKeyboardButton(text="💧 Фильтр-кофе Эфиопия (280 ₽)", callback_data="pre_drink_Batch Filter_280")],
        [InlineKeyboardButton(text="🧊 Айс-Латте соленая карамель (390 ₽)", callback_data="pre_drink_Ice Latte_390")],
        [InlineKeyboardButton(text="⬅️ Отмена", callback_data="main_menu")]
    ])
    
    await call.message.edit_text(f"⏳ <b>Предзаказ кофе к приходу:</b>{warning}\n\nВыберите напиток:", parse_mode="HTML", reply_markup=kb)
    await call.answer()

@router.callback_query(PreorderState.waiting_for_drink, F.data.startswith("pre_drink_"))
async def cb_preorder_drink(call: CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    drink_name = parts[2]
    price = int(parts[3])
    
    await state.update_data(drink=drink_name, price=price)
    await state.set_state(PreorderState.waiting_for_time)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Через 10 минут", callback_data="time_10m")],
        [InlineKeyboardButton(text="⚡ Через 15 минут", callback_data="time_15m")],
        [InlineKeyboardButton(text="🕒 Через 30 минут", callback_data="time_30m")],
        [InlineKeyboardButton(text="🌅 К открытию (08:00)", callback_data="time_0800")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="start_preorder")]
    ])
    
    await call.message.edit_text(
        f"Вы выбрали: <b>{drink_name}</b> ({price} ₽)\n\nКогда вы подойдете в кофейню?",
        parse_mode="HTML",
        reply_markup=kb
    )
    await call.answer()

@router.callback_query(PreorderState.waiting_for_time, F.data.startswith("time_"))
async def cb_preorder_confirm(call: CallbackQuery, state: FSMContext):
    time_choice = call.data.replace("time_", "")
    time_label = {
        "10m": "через 10 минут",
        "15m": "через 15 минут",
        "30m": "через 30 минут",
        "0800": "к открытию в 08:00"
    }.get(time_choice, "к приходу")
    
    data = await state.get_data()
    drink = data.get("drink", "Фильтр-кофе")
    price = data.get("price", 280)
    user = call.from_user
    username = f"@{user.username}" if user.username else f"ID {user.id}"
    
    order_data = {
        "user_identifier": str(user.id),
        "client_name": user.full_name,
        "phone": username,
        "order_type": "pickup",
        "pickup_time": time_label,
        "items_json": json.dumps([{"title": drink, "quantity": 1, "price_rub": price}], ensure_ascii=False),
        "total_amount_rub": price,
        "notes": f"Предзаказ навынос: {time_label}"
    }
    order_id = database.create_order(order_data)
    await state.clear()
    
    await call.message.edit_text(
        f"🎯 <b>Предзаказ #{order_id} передан бариста!</b>\n\n"
        f"Напиток: <b>{drink}</b>\n"
        f"Готовность: <b>{time_label}</b>\n"
        f"Сумма: <b>{price} ₽</b> (оплата при получении или через СБП)\n\n"
        f"📍 Ждем вас: Покровка, 12. Ваш напиток будет горячим и свежим!",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
        ])
    )
    await call.answer()

# --- 1-Click Repeat Order ---
@router.callback_query(F.data == "reorder_last")
async def cb_reorder_last(call: CallbackQuery):
    user_id = str(call.from_user.id)
    last_order = database.get_last_user_order(user_id)
    
    if not last_order:
        await call.message.edit_text(
            "ℹ️ У вас еще нет истории заказов. Закажите ваш первый кофе в каталоге!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="☕ Перейти к сортам зерна", callback_data="cat_beans")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
            ])
        )
        await call.answer()
        return

    # Clone last order
    new_order = {
        "user_identifier": user_id,
        "client_name": last_order["client_name"],
        "phone": last_order["phone"],
        "order_type": last_order["order_type"],
        "pickup_time": last_order["pickup_time"],
        "items_json": last_order["items_json"],
        "total_amount_rub": last_order["total_amount_rub"],
        "notes": f"1-Click повтор заказа #{last_order['id']}"
    }
    new_id = database.create_order(new_order)
    
    await call.message.edit_text(
        f"🔁 <b>Заказ успешно повторен (ID #{new_id})!</b>\n\n"
        f"Состав: <code>{last_order['items_json']}</code>\n"
        f"Сумма: <b>{last_order['total_amount_rub']} ₽</b>\n\n"
        f"Бариста уже занимается повторным заказом!",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
    )
    await call.answer()

@router.callback_query(F.data == "cafe_info")
async def cb_cafe_info(call: CallbackQuery):
    status = "🟢 Сейчас открыто" if is_cafe_open() else "🔴 Сейчас закрыто (откроемся в 08:00)"
    text = (
        "📍 <b>Кофейня Roast Lab Coffee:</b>\n\n"
        "🏛 <b>Адрес:</b> Москва, ул. Покровка, д. 12 (м. Чистые пруды / Китай-город)\n"
        "🕒 <b>Режим работы:</b> 08:00 – 22:00 без выходных\n"
        f"⚡ <b>Статус:</b> {status}\n\n"
        f"По всем вопросам: {OWNER_USERNAME}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ])
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()

def create_bot_and_dispatcher():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    return bot, dp

async def main():
    bot, dp = create_bot_and_dispatcher()
    print("Starting Roast Lab Telegram Bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
