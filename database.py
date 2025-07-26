import sqlite3
from datetime import date

DB_FILE = "cineblocker.db"

def init_db():
    """Инициализирует базу данных и создает таблицу, если она не существует."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                activity_date TEXT PRIMARY KEY,
                total_seconds INTEGER NOT NULL
            )
        """)
        conn.commit()

def get_today_activity() -> int:
    """Получает общее количество активных секунд за сегодня."""
    today_str = date.today().isoformat()
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT total_seconds FROM activity_log WHERE activity_date = ?", (today_str,))
        result = cursor.fetchone()
        return result[0] if result else 0

def save_today_activity(total_seconds: int):
    """Обновляет или вставляет запись об общем времени активности за сегодня."""
    today_str = date.today().isoformat()
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # "INSERT OR REPLACE" - удобная команда SQLite для этой задачи
        cursor.execute("""
            INSERT OR REPLACE INTO activity_log (activity_date, total_seconds)
            VALUES (?, ?)
        """, (today_str, total_seconds))
        conn.commit()
    print(f"💾 Данные сохранены. Общее время за сегодня: {total_seconds // 60} мин {total_seconds % 60} сек.")