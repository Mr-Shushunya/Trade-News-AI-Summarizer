from telegram import ReplyKeyboardMarkup, KeyboardButton

# Экран 2: Выбор активов
def assets_keyboard():
    return ReplyKeyboardMarkup(
        [["Ввести вручную", "Посмотреть подборки"], ["Закончить подбор"]],
        resize_keyboard=True
    )

# Подборки активов
def collections_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["Криптовалюты", "Популярные валюты"],
            ["Акции РФ", "Назад"]
        ],
        resize_keyboard=True
    )

# Экран 3: Периодичность
def frequency_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["Посмотреть один раз", "Раз в 5 мин"],
            ["Раз в 30 мин", "Раз в час"],
            ["1 раз в день"]
        ],
        resize_keyboard=True
    )

# Экран 4: Главное меню
def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        [["Запросить новости", "Настроить бота"], ["Обратиться в техподдержку"]],
        resize_keyboard=True
    )

# Экран 5: Настройки
def settings_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["Подписаться на активы", "Отписаться от активов"],
            ["Настроить частоту рассылки", "Назад"]
        ],
        resize_keyboard=True
    )