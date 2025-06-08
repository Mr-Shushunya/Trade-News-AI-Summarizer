import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

def fetch_page(url):
    """Получение HTML-страницы с новостями"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Ошибка при получении страницы {url}: {e}")
        return None

def parse_date(date_str):
    """Парсинг даты с учетом разных форматов"""
    if not date_str or 'Главная' in date_str:
        return None
    try:
        date_str = date_str.replace('\n', '').strip()
        parts = date_str.split(',')

        if len(parts) == 2:  # Формат "07 июн, 09:00"
            day, time = parts[0].strip(), parts[1].strip()
            month_str = day.split()[1]
            day = day.split()[0]

            months_short = {
                'янв': 'Jan', 'фев': 'Feb', 'мар': 'Mar', 'апр': 'Apr',
                'май': 'May', 'июн': 'Jun', 'июл': 'Jul', 'авг': 'Aug',
                'сен': 'Sep', 'окт': 'Oct', 'ноя': 'Nov', 'дек': 'Dec'
            }
            month_en = months_short.get(month_str, 'Jan')
            date_str = f"{day} {month_en} {time}"

            parsed_date = datetime.strptime(date_str, '%d %b %H:%M')
            parsed_date = parsed_date.replace(year=datetime.now().year)
            return parsed_date.isoformat()
        elif ':' in date_str:  # Формат "09:00"
            time = date_str.strip()
            parsed_date = datetime.strptime(time, '%H:%M')
            parsed_date = parsed_date.replace(year=datetime.now().year, month=datetime.now().month, day=datetime.now().day)
            return parsed_date.isoformat()
        else:
            return None
    except Exception as e:
        print(f"Ошибка при парсинге даты {date_str}: {e}")
        return None

def parse_article_details(url):
    """Парсинг дополнительной информации со страницы статьи"""
    html = fetch_page(url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')
    details = {}

    # Извлечение полного текста
    text_elem = soup.find('div', class_='article__text')
    details['full_text'] = text_elem.text.strip() if text_elem else None

    # Извлечение даты публикации из заголовка статьи
    date_elem = soup.find('time', class_='article__header__date')
    details['publication_date'] = date_elem['datetime'] if date_elem and date_elem.get('datetime') else None

    # Извлечение авторов
    authors = soup.select('.article__authors__author__name')
    details['authors'] = [author.text.strip() for author in authors] if authors else []

    # Извлечение тегов
    tags = soup.select('.article__tags__item')
    details['tags'] = [tag.text.strip() for tag in tags] if tags else []

    # Извлечение компаний и их данных (например, из слайдера)
    companies = []
    company_slides = soup.select('.q-item__company')
    for company in company_slides:
        name = company.find('span', class_='q-item__company__name')
        short_name = company.find('span', class_='q-item__company__name-short')
        change = company.find('span', class_='q-item__company__change')
        companies.append({
            'name': name.text.strip() if name else None,
            'short_name': short_name.text.strip() if short_name else None,
            'change': change.text.strip() if change else None
        })
    details['companies'] = companies if companies else None

    return details

def parse_rbc_trading():
    URL = "https://www.rbc.ru/quote/"
    results = []

    # Парсинг основной страницы
    html = fetch_page(URL)
    if not html:
        return results

    soup = BeautifulSoup(html, 'html.parser')
    main_content = soup.find('main', id='maincontent')
    if not main_content:
        print("Не найден основной контент на странице")
        return results

    articles = main_content.find_all('div', class_='q-item')
    if not articles:
        print("Не найдены статьи на странице")
        return results

    for article in articles:
        try:
            title_elem = article.find('span', class_='q-item__title')
            title = title_elem.text.strip() if title_elem else None

            url_elem = article.find('a', class_='q-item__link')
            url = url_elem['href'] if url_elem and url_elem.get('href') else ''
            if url and not url.startswith('http'):
                url = 'https://www.rbc.ru' + url

            date_block = article.find('span', class_='q-item__date__text')
            date_str = date_block.text.strip() if date_block else None
            iso_date = parse_date(date_str) if date_str else None

            description_elem = article.find('span', class_='q-item__description')
            description = description_elem.text.strip() if description_elem else None

            image_elem = article.find('img', class_='q-item__image')
            image_url = image_elem['src'] if image_elem and image_elem.get('src') else None

            # Пропускаем статью, если нет заголовка или URL
            if not title or not url:
                continue

            # Парсинг дополнительной информации из ссылки
            article_details = parse_article_details(url)

            results.append({
                'title': title,
                'url': url,
                'date': iso_date,
                'date_original': date_str,
                'description': description,
                'image_url': image_url,
                'source': 'RBC Трейдинг',
                'details': article_details
            })
        except Exception as e:
            print(f"Ошибка при парсинге статьи: {e}")
            continue

    return results

def save_to_json1(data, filename='rbc_trading.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4, default=str)

