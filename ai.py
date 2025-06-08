import requests
import time
import uuid
import json
from client import send_message

SYSTEM_PROMPT = """Ты — профессиональный финансовый аналитик, специализирующийся на обработке новостных потоков. Твоя задача — проанализировать пачку входящих новостей (20-30 шт.) о фондовом рынке и выдать на выходе только уникальные новостные события.

**Критерий уникальности:**
Новость считается уникальной, если она описывает новое событие, тему или тренд, отличающееся по своей основной сути от других новостей.

**Инструкции:**
1. Агрегируй новости об одном событии/теме в одну запись
2. Формулируй краткую обобщающую фразу
3. Противоположные мнения выделяй отдельно.
4. Если одно из противоположных мнений доминирует (например, гораздо больше новостей про то, что юань падает, чем растет), нужно подчеркнуть, какое из мнений преобладает
5. Выводи ТОЛЬКО список уникальных событий в формате:
   - Событие 1
   - Событие 2
   - ...
6. Выводи новости в единой стилистике, где обязательно будет подлежащее и сказуемое
7. Все новости имеют одинаковую правдивость. Если перед тобой две противоречивые новости, ты не можешь сам решать, какая из них правдивая: ты обязан представить пользователю обе точки зрения.
8. Обращай внимание на даты новостей: если перед тобой несколько новостей от разных дат, группируй их от самой старой к самой новой и обязательно пиши дату и время каждой новости.
9. Пронумеруй все новости
10. Отдельным списком выведи все категории, относящиеся к каждой новости. Если ни одна из отправленных мною категорий не подходит, оставь пустую строку.
11. Строго придерживайся приведенного в примере формата выхода!

**Пример:**
Вход:
Категории: ноунейм груп, tesla, трамп
Новости: 
1 новость "Ноунейм Груп упала на 3%" от 24.05.2024 14:07, 1 новость "Ноунейм Групп подросла на 7%" от 24.05.2024 в 16:08, 10 новостей "Юань может укрепиться", 1 новость "Возможен обвал юаня", 3 новости о том, что Трамп и Маск рассорились и на фоне этого обвалились акции Tesla
Выход:
1. 24 мая днем Ноунейм Груп упала на 3%, а за следующие два часа отросла на 7
2. Большинство новостных порталов предрекает укрепление юаня
3. Некоторые эксперты отмечают риск ослабления юаня
4. Акции Tesla падают на фоне ссоры Илона Маска с Дональдом Трампом
1. ноунейм груп
2. 
3.
4. tesla, трамп
"""


# Конфигурация API OrionSoft
API_URL = "https://gpt.orionsoft.ru/api/External/"
API_KEY = "OrVrQoQ6T43vk0McGmHOsdvvTiX446RJ"
OPERATING_SYSTEM_CODE = 12
USER_DOMAIN_NAME = "Teamt9tNEoZNXkX6"
AI_MODEL_CODE = 1 

# Категоории, по которым интересны новости
news_categories = "SBER", "СПБ Биржа", "Доллар", "Трамп"

def generate_dialog_identifier():
    """Генерирует уникальный идентификатор диалога"""
    return f"{USER_DOMAIN_NAME}_{uuid.uuid4().hex}"

def post_new_request(dialog_identifier, message):
    """Отправляет новый запрос в API"""
    url = API_URL + "PostNewRequest"
    payload = {
        "operatingSystemCode": OPERATING_SYSTEM_CODE,
        "apiKey": API_KEY,
        "userDomainName": USER_DOMAIN_NAME,
        "dialogIdentifier": dialog_identifier,
        "aiModelCode": AI_MODEL_CODE,
        "Message": SYSTEM_PROMPT + "\n\n" + message
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"isSuccess": False, "message": str(e)}

def get_new_response(dialog_identifier):
    """Получает ответ от API и извлекает только responseMessage"""
    url = API_URL + "GetNewResponse"
    payload = {
        "operatingSystemCode": OPERATING_SYSTEM_CODE,
        "apiKey": API_KEY,
        "Dialogidentifier": dialog_identifier
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        response_data = response.json()
        
        # Извлекаем responseMessage из контекста
        if response_data.get('status', {}).get('isSuccess', False):
            context = response_data.get('data', {}).get('context', [])
            if context:
                # Берем последнее сообщение из контекста
                return context[-1].get('responseMessage', '')
        return ""
    except Exception as e:
        print(f"Ошибка при получении ответа: {str(e)}")
        return ""

def complete_session(dialog_identifier):
    """Завершает сессию и очищает контекст"""
    url = API_URL + "CompleteSession"
    payload = {
        "operatingSystemCode": OPERATING_SYSTEM_CODE,
        "apiKey": API_KEY,
        "Dialogidentifier": dialog_identifier  # Исправлено на Documentidentifier
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"isSuccess": False, "message": str(e)}

def get_unique_news(news_text):
    """Получает уникальные новости через API OrionSoft"""
    dialog_identifier = generate_dialog_identifier()
    print(f"Идентификатор диалога: {dialog_identifier}")
    
    # Отправляем запрос
    post_response = post_new_request(dialog_identifier, news_text)
    print(f"Ответ на запрос: {post_response}")
    
    if not post_response.get("isSuccess", False):
        error_msg = post_response.get('message', 'Неизвестная ошибка')
        return f"Ошибка отправки запроса: {error_msg}"
    
    # Ожидаем ответ (максимум 10 попыток)
    for i in range(20):
        print(f"Попытка #{i+1} получения ответа...")
        time.sleep(10)
        
        response_message = get_new_response(dialog_identifier)  # Теперь получаем только текст
        
        if response_message:  # Если получили непустой ответ
            complete_session(dialog_identifier)
            return response_message.strip()
        else:
            print("Ответ еще не готов, продолжаем ожидание...")
    
    complete_session(dialog_identifier)
    return "Превышено время ожидания ответа от сервера"

    
def get_news():
    # Загрузка новостей из JSON-файла
    try:
        with open('rbc_trading.json', 'r', encoding='utf-8') as f:
            news_data = json.load(f)
    except FileNotFoundError:
        print("Файл rbc_trading.json не найден!")
        return
    except Exception as e:
        print(f"Ошибка при чтении файла: {str(e)}")
        return

    # Извлекаем тексты новостей
    news_texts = []
    for item in news_data:
        if 'details' in item and 'full_text' in item['details']:
            news_texts.append(item['details']['full_text'])
    
    if not news_texts:
        print("В файле нет новостей с полем full_text")
        return
    
    # Объединяем все новости в одну строку
    news_text = "\n".join(news_texts)
    
    # Проверка длины запроса
    total_length = len(SYSTEM_PROMPT) + len(news_text)
    print(f"Загружено новостей: {len(news_texts)}")
    print(f"Общая длина запроса: {total_length} символов")
    if total_length > 30000:
        print("Предупреждение: Запрос очень длинный, возможны проблемы с обработкой")
    
    print("\nОбработка новостей...\n")

    #required_categories = все категории из БД
    required_categories = ["Tesla", "Центральный банк", "Ключевая ставка", "Илон Маск", "Дональд Трамп"]
    
    result = get_unique_news("Категории:"+str(required_categories)+"\nНовости: \n"+news_text)
    
    return result

#if __name__ == "__main__":
 #   main()