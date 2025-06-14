import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)
from keyboards import *
from utils import *
from news_service import get_news_for_assets
from telegram import ReplyKeyboardRemove 

from CombineParceModule import parse_news
from ai import get_news


(
    STATE_SELECT_ASSETS,        # Экран 2: выбор активов
    STATE_SET_FREQUENCY,        # Экран 3: выбор периодичности
    STATE_MAIN_MENU,            # Экран 4: главное меню
    STATE_BOT_SETTINGS,         # Экран 5: настройки
    STATE_MANUAL_INPUT,         # Ручной ввод активов
    STATE_UNSUBSCRIBE           # Отписка от активов
) = range(6)

# Подборки активов
COLLECTIONS = {
    "Криптовалюты": ["BTC", "ETH", "BNB", "XRP", "ADA"],
    "Популярные валюты": ["USD", "EUR", "JPY", "GBP", "CNY"],
    "Акции РФ": ["GAZP", "SBER", "LKOH", "MGNT", "ROSN"]
}


# Обработчик /start - отсюда начинается ВСЕ
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔍 Какие активы вас интересуют?",
        reply_markup=assets_keyboard()
    )
    return STATE_SELECT_ASSETS


# ===ГЛАВНОЕ МЕНЮ===

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏠 Главное меню:", reply_markup=main_menu_keyboard())
    return STATE_MAIN_MENU


# 0. Возврат в главное меню

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в главное меню"""
    await main_menu(update, context)
    return STATE_MAIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена операции"""
    await update.message.reply_text("🚫 Операция отменена")
    await main_menu(update, context)
    return STATE_MAIN_MENU


# 1. Запрос новостей
async def fetch_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    subs = load_subscriptions()
    await update.message.reply_text(get_news(subs), reply_markup=main_menu_keyboard())


# 2. Настройки
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚙️ Настройки:", reply_markup=settings_keyboard())
    return STATE_BOT_SETTINGS

# 2.1. Подписаться
async def settings_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переход к подписке на активы из настроек"""
    await update.message.reply_text(
        "🔍 Какие активы вас интересуют?",
        reply_markup=assets_keyboard()
    )
    return STATE_SELECT_ASSETS

#Ручной ввод

async def ask_manual_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запрос ручного ввода активов с кнопкой отмены"""
    await update.message.reply_text(
        "📝 Введите активы через запятую:\n\nПример: BTC, ETH, AAPL",
        reply_markup=ReplyKeyboardMarkup([["Отменить ввод"]], resize_keyboard=True)
    )
    return STATE_MANUAL_INPUT

async def handle_manual_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ручного ввода активов"""
    user_id = update.effective_user.id
    assets = update.message.text.split(',')
    added = add_assets(user_id, assets)
    
    # Проверка на случай пустого ввода
    if not added:
        message = "ℹ️ Все активы уже были добавлены ранее или ввод пуст."
    else:
        message = f"✅ Добавлено активов: {len(added)}\nНовые активы: {', '.join(added)}"
    
    # Получаем полный список активов пользователя
    subs = load_subscriptions()
    user_assets = subs.get(str(user_id), {}).get("assets", [])
    
    if user_assets:
        message += f"\n📋 Все ваши активы: {', '.join(user_assets)}"
    
    await update.message.reply_text(
        message,
        reply_markup=assets_keyboard()
    )
    return STATE_SELECT_ASSETS

#Устаревший вариант обработки ручного ввода
""""
async def handle_manual_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    assets = [a.strip() for a in update.message.text.split(",")]
    add_assets(update.effective_user.id, assets)
    await update.message.reply_text("✅ Активы добавлены!", reply_markup=assets_keyboard())
    return STATE_SELECT_ASSETS
"""

#Подборки

async def show_collections(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ доступных подборок"""
    await update.message.reply_text(
        "📚 Выберите готовую подборку активов:",
        reply_markup=collections_keyboard()
    )
    return STATE_SELECT_ASSETS

async def handle_collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора готовой подборки"""
    collection_name = update.message.text
    collection_map = {
        "Криптовалюты": ["BTC", "ETH", "BNB", "XRP", "ADA"],
        "Популярные валюты": ["USD", "EUR", "JPY", "GBP", "CNY"],
        "Акции РФ": ["GAZP", "SBER", "LKOH", "MGNT", "ROSN"]
    }
    
    if collection_name in collection_map:
        user_id = update.effective_user.id
        add_assets(user_id, collection_map[collection_name])
        await update.message.reply_text(
            f"✅ Подборка «{collection_name}» добавлена!",
            reply_markup=assets_keyboard()
        )
    return STATE_SELECT_ASSETS

async def back_to_assets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к основному экрану выбора активов"""
    await update.message.reply_text(
        "🔍 Какие активы вас интересуют?",
        reply_markup=assets_keyboard()
    )
    return STATE_SELECT_ASSETS


# 2.2. Отписаться
async def settings_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка отписки от активов"""
    user_id = update.effective_user.id
    subs = load_subscriptions()
    assets = subs.get(str(user_id), {}).get("assets", [])
    
    if not assets:
        await update.message.reply_text("❌ У вас нет активов для отписки!")
        return STATE_BOT_SETTINGS
    
    # Формируем клавиатуру с текущими активами
    keyboard = [[asset] for asset in assets] + [["Отписаться от всех"], ["Назад"]]
    await update.message.reply_text(
        "❌ Выберите активы для отписки:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return STATE_UNSUBSCRIBE

async def handle_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора активов для отписки"""
    user_id = update.effective_user.id
    choice = update.message.text
    subs = load_subscriptions()
    user_subs = subs.get(str(user_id), {})
    
    if choice == "Отписаться от всех":
        user_subs["assets"] = []
        await update.message.reply_text("❌ Вы отписались от всех активов!")
    elif choice == "Назад":
        await settings(update, context)
        return STATE_BOT_SETTINGS
    else:
        if choice in user_subs.get("assets", []):
            user_subs["assets"].remove(choice)
            await update.message.reply_text(f"❌ Вы отписались от {choice}!")
    
    save_subscriptions(subs)
    await settings(update, context)
    return STATE_BOT_SETTINGS


# 3. Техподдержка
async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✉️ Опишите проблему разработчику: @Mr_Shushunya")




''' # Завершение подписки -> выбор периодичности
async def finish_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏱ Выберите периодичность:", reply_markup=frequency_keyboard())
    return STATE_SET_FREQUENCY
'''

""""async def settings_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Добавляем опцию "Отключить рассылку"
    keyboard = [
        ["Посмотреть один раз", "Раз в 5 мин"],
        ["Раз в 30 мин", "Раз в час"],
        ["1 раз в день", "Отключить рассылку"],
        ["Назад"]
    ]
    await update.message.reply_text(
        "⏱ Выберите периодичность:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return STATE_SET_FREQUENCY
"""

"""async def set_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    frequency = update.message.text
    frequency_map = {
        "Посмотреть один раз": "once",
        "Раз в 5 мин": "5min",
        "Раз в 30 мин": "30min",
        "Раз в час": "hourly",
        "1 раз в день": "daily",
        "Отключить рассылку": "off"
    }"""



# Парсинг новостей каждые 5 секунд.
# На текущий момент не реализовано: не успели связать модуль бота с модулем парсинга.
# Планирую реализовать в июне 2025.
#
'''
async def update_news():
    while True:
        await asyncio.sleep(5)
'''

if __name__ == "__main__":
    app = Application.builder().token("iwontshowyoumytoken").build()
    
    conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        STATE_SELECT_ASSETS: [
            MessageHandler(filters.Regex(r"^Ввести вручную$"), ask_manual_input),
            MessageHandler(filters.Regex(r"^Посмотреть подборки$"), show_collections),
            MessageHandler(filters.Regex(r"^Закончить подбор$"), back_to_main),
            # Добавляем обработчики для подборок
            MessageHandler(filters.Regex(r"^(Криптовалюты|Популярные валюты|Акции РФ)$"), handle_collection),
            # Добавляем обработчик для кнопки "Назад"
            MessageHandler(filters.Regex(r"^Назад$"), back_to_assets)
        ],
        STATE_MANUAL_INPUT: [
            MessageHandler(filters.Regex(r"^Отменить ввод$"), back_to_assets),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_manual_input)
        ],
        STATE_MAIN_MENU: [
            MessageHandler(filters.Regex(r"^Запросить новости$"), fetch_news),
            MessageHandler(filters.Regex(r"^Настроить бота$"), settings),
            MessageHandler(filters.Regex(r"^Обратиться в техподдержку$"), support)
        ],
        STATE_BOT_SETTINGS: [
            MessageHandler(filters.Regex(r"^Подписаться на активы$"), settings_subscribe),
            MessageHandler(filters.Regex(r"^Отписаться от активов$"), settings_unsubscribe),
            #MessageHandler(filters.Regex(r"^Настроить частоту рассылки$"), settings_frequency),
            MessageHandler(filters.Regex(r"^Назад$"), back_to_main)
        ],
        # Добавляем состояние для отписки
        STATE_UNSUBSCRIBE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unsubscribe)
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    app.run_polling()
