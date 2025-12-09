# fix_database.py
import sqlite3
import database

def fix_database():
    """Исправляет проблемы в базе данных"""
    conn = sqlite3.connect(database.DB_NAME)
    cursor = conn.cursor()
    
    # Исправляем структуру таблицы student_progress
    try:
        cursor.execute("ALTER TABLE student_progress ADD COLUMN completed BOOLEAN DEFAULT FALSE")
    except:
        pass  # Колонка уже существует
    
    # Пробуем добавить уникальное ограничение (если не существует)
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_student_topic ON student_progress(student_id, topic_id)")
    except:
        pass
    
    # Удаляем дублирующиеся записи прогресса
    cursor.execute("""
        DELETE FROM student_progress 
        WHERE id NOT IN (
            SELECT MIN(id) 
            FROM student_progress 
            GROUP BY student_id, topic_id
        )
    """)
    
    conn.commit()
    conn.close()
    print("База данных исправлена!")

if __name__ == "__main__":
    fix_database()