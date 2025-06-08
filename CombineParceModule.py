from rbk import parse_rbc_trading
from rbk import save_to_json1
from vedomosti import parse_rss_feeds
from vedomosti import save_to_json
import time

def parse_news():
    #vedomosti
    print("Парсинг раздела Трейдинг RBC...")
    data = parse_rbc_trading()
    save_to_json1(data)
    print(f"Сохранено {len(data)} статей в rbc_trading.json")

    # rbc
    rss_urls = [
        'https://www.vedomosti.ru/rss/rubric/finance/banks',
        'https://www.vedomosti.ru/rss/rubric/finance/markets.xml'
    ]

    print("Начало парсинга...")
    start_time = time.time()
    all_results = parse_rss_feeds(rss_urls, max_articles_per_feed=5, max_workers=2)
    end_time = time.time()

    save_to_json(all_results)
    print(f"Сохранено {len(all_results)} статей в vedomosti_rss.json")
    print(f"Время выполнения: {end_time - start_time:.2f} секунд")