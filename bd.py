import asyncpg
import logging
from datetime import datetime, timedelta
import json

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Строка подключения к БД
DB_CONNECTION_STRING = "postgresql://postgres:password@localhost/NewsAggregator"


class NewsDatabase:
    def __init__(self, database_url):
        self.database_url = database_url
        self.conn = None  # Это атрибут, который будет хранить подключение

    async def connect(self):
        """Устанавливаем соединение с базой данных"""
        self.conn = await asyncpg.connect(self.database_url)
        print("Соединение с базой данных установлено.")

    async def close(self):
        """Закрываем соединение с базой данных"""
        if self.conn:
            await self.conn.close()
            print("Соединение с базой данных закрыто.")

    async def write_news(self, title, url, full_text, category_id):
        """Сохраняем новость в базу данных"""
        try:
            query = """
            INSERT INTO News (title, url, fulltext, category_id)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (url) DO NOTHING;  -- Избегаем дублей по URL
            """
            # Проверяем, что соединение существует, прежде чем выполнить запрос
            if self.conn:
                await self.conn.execute(query, title, url, full_text, category_id)
                print(f"Новость '{title}' успешно сохранена в БД.")
            else:
                print("Соединение с базой данных не установлено.")
        except Exception as e:
            print(f"Ошибка при сохранении новости в БД: {e}")

    async def read_news(self):
        """Читаем новости из базы данных"""
        async with self.pool.acquire() as conn:
            # Получаем все новости
            news = await conn.fetch("SELECT full_text FROM news")
            logger.info(f"Fetched {len(news)} news from the database.")
            return news
    
    async def read_compressed_news(self):
        """Читаем новости из базы данных"""
        async with self.pool.acquire() as conn:
            # Получаем все новости
            news = await conn.fetch("SELECT summary FROM news")
            logger.info(f"Fetched {len(news)} news from the database.")
            return news

    async def check_news_relevance(self, news_id: int):
        """Проверяем актуальность новости"""
        async with self.pool.acquire() as conn:
            # Получаем дату создания новости
            created_at = await conn.fetchval(
                "SELECT created_at FROM news WHERE id = $1", news_id
            )

            if not created_at:
                logger.error(f"News with ID {news_id} not found.")
                return False

            # Проверяем, если новость старше 1 часа
            is_relevant = created_at > datetime.utcnow() - timedelta(hours=1)
            if is_relevant:
                logger.info(f"News ID {news_id} is relevant.")
            else:
                logger.info(f"News ID {news_id} is outdated.")
            return is_relevant

    async def update_news_summary(self, news_id: int, new_summary: str):
        """Обновляем пересказ новости"""
        async with self.pool.acquire() as conn:
            # Обновляем пересказ (summary)
            result = await conn.execute(
                "UPDATE news SET summary = $1 WHERE id = $2",
                new_summary, news_id
            )

            if result:
                logger.info(f"Summary for news ID {news_id} updated successfully.")
            else:
                logger.error(f"Failed to update summary for news ID {news_id}.")

    async def news_exists_recent(self, title: str) -> bool:
        """Проверяет, существует ли новость с таким заголовком за последний час"""
        one_hour_ago = datetime.utcnow() - timedelta(hours=24)
        result = await self.conn.fetchrow(
            """
            SELECT 1 FROM News
            WHERE title = $1 AND created_at >= $2
            LIMIT 1
            """,
            title,
            one_hour_ago,
        )
        return result is not None

async def main():
    db = NewsDatabase(DB_CONNECTION_STRING)

    # Подключаемся к базе данных
    await db.connect()

    # Пример записи новости
    await db.write_news(
        title="New Article Title",
        url="http://example.com/news1",
        fulltext="This is the full content of the news...",
        category_id=10 # Здесь вставьте нужный ID категории
    )

    # Пример чтения новостей
    news = await db.read_news()
    logger.info(f"News in database: {news}")

    # Проверяем актуальность новости
    news_id_to_check = 1  # Пример ID новости
    is_relevant = await db.check_news_relevance(news_id_to_check)
    logger.info(f"Is news ID {news_id_to_check} relevant? {is_relevant}")

    # Обновляем пересказ
    new_summary = "This is the updated summary of the news."
    await db.update_news_summary(news_id_to_check, new_summary)

    # Закрываем соединение
    await db.close()


if __name__ == "__main__":
    # Запускаем асинхронный цикл
    import asyncio

    asyncio.run(main())
