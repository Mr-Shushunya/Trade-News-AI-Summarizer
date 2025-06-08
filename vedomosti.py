import feedparser
import requests
from bs4 import BeautifulSoup
import json
from concurrent.futures import ThreadPoolExecutor
import time


def fetch_page(url):
    """Получение HTML-страницы"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Ошибка при получении страницы {url}: {e}")
        return None


def parse_article_details(url):
    """Парсинг дополнительной информации со страницы статьи"""
    html = fetch_page(url)
    if not html:
        return None
    soup = BeautifulSoup(html, 'html.parser')
    details = {}

    # Извлечение полного текста
    text_elem = soup.find('div', class_='article__body')
    details['full_text'] = text_elem.text.strip() if text_elem else "Текст не найден"

    # Извлечение изображений
    images = soup.select('img.article__image')
    details['images'] = [img['src'] for img in images if img.get('src')] if images else []

    return details


def process_article(item):
    """Обработка одной статьи с парсингом страницы"""
    article = {
        'title': item.get('title', ''),
        'link': item.get('link', ''),
        'guid': item.get('guid', ''),
        'author': item.get('author', ''),
        'category': item.get('category', ''),
        'description': item.get('description', ''),
        'pubDate': item.get('published', ''),
        'image_url': item.get('enclosure', {}).get('url', ''),
    }

    if article['link']:
        print(f"Парсинг страницы: {article['link']}")
        details = parse_article_details(article['link'])
        if details:
            article.update(details)

    time.sleep(1)  # Задержка между запросами
    return article


def parse_rss_feeds(rss_urls, max_articles_per_feed=5, max_workers=2):
    """Парсинг всех RSS-лент и обработка ссылок"""
    all_results = []

    for url in rss_urls:
        print(f"Парсинг RSS-ленты: {url}")
        feed = feedparser.parse(url)
        if not feed.entries:
            print(f"Нет данных в ленте: {url}")
            continue

        # Ограничение количества статей
        entries_to_process = feed.entries[:max_articles_per_feed]

        # Параллельная обработка с меньшим числом потоков
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(process_article, entries_to_process))
        all_results.extend(results)
        time.sleep(2)  # Задержка между лентами

    return all_results


def save_to_json(data, filename='vedomosti_rss.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


