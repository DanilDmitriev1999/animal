#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы с данными AI Learning Platform
Демонстрирует основные операции с БД через psycopg2
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os


def get_connection():
    """Получение подключения к БД"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'ai_learning_db'),
        user=os.getenv('DB_USER', 'user'),
        password=os.getenv('DB_PASSWORD', 'password')
    )


def test_users_table():
    """Тестирование таблицы пользователей"""
    print("🔍 Тестирование таблицы users...")
    
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Получение всех пользователей
    cursor.execute("""
        SELECT id, email, first_name, last_name, role, ai_personality, 
               created_at, is_active 
        FROM users
    """)
    users = cursor.fetchall()
    
    print(f"  Найдено пользователей: {len(users)}")
    for user in users:
        print(f"    • ID: {user['id']}, Email: {user['email']}, "
              f"Имя: {user['first_name']} {user['last_name']}, "
              f"Роль: {user['role']}, AI стиль: {user['ai_personality']}")
    
    cursor.close()
    conn.close()


def test_tracks_and_modules():
    """Тестирование таблиц треков и модулей"""
    print("\n🔍 Тестирование таблиц tracks и modules...")
    
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Получение треков с модулями
    cursor.execute("""
        SELECT 
            t.id as track_id,
            t.title as track_title,
            t.difficulty_level,
            t.estimated_duration_hours,
            m.id as module_id,
            m.title as module_title,
            m.order_index
        FROM tracks t
        LEFT JOIN modules m ON t.id = m.track_id
        ORDER BY t.id, m.order_index
    """)
    results = cursor.fetchall()
    
    # Группировка по трекам
    tracks_data = {}
    for row in results:
        track_id = row['track_id']
        if track_id not in tracks_data:
            tracks_data[track_id] = {
                'title': row['track_title'],
                'difficulty': row['difficulty_level'],
                'duration': row['estimated_duration_hours'],
                'modules': []
            }
        
        if row['module_id']:
            tracks_data[track_id]['modules'].append({
                'id': row['module_id'],
                'title': row['module_title'],
                'order': row['order_index']
            })
    
    print(f"  Найдено треков: {len(tracks_data)}")
    for track_id, track in tracks_data.items():
        print(f"    • Трек {track_id}: {track['title']} "
              f"(уровень {track['difficulty']}, {track['duration']}ч)")
        for module in track['modules']:
            print(f"      - Модуль {module['order']}: {module['title']}")
    
    cursor.close()
    conn.close()


def test_lessons():
    """Тестирование таблицы уроков"""
    print("\n🔍 Тестирование таблицы lessons...")
    
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT 
            l.id,
            l.title,
            l.lesson_type,
            l.estimated_minutes,
            l.order_index,
            m.title as module_title,
            t.title as track_title
        FROM lessons l
        JOIN modules m ON l.module_id = m.id
        JOIN tracks t ON m.track_id = t.id
        ORDER BY t.id, m.order_index, l.order_index
    """)
    lessons = cursor.fetchall()
    
    print(f"  Найдено уроков: {len(lessons)}")
    for lesson in lessons:
        print(f"    • {lesson['track_title']} → {lesson['module_title']} → "
              f"{lesson['title']} ({lesson['lesson_type']}, {lesson['estimated_minutes']}мин)")
    
    cursor.close()
    conn.close()


def test_chat_functionality():
    """Тестирование функционала чата"""
    print("\n🔍 Тестирование функционала chat_messages...")
    
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Добавляем тестовые сообщения
    test_messages = [
        {
            'user_id': 1,
            'session_id': 'test-session-123',
            'agent_type': 'dashboard',
            'context_data': '{"screen": "dashboard"}',
            'role': 'user',
            'content': 'Привет! Покажи мне доступные курсы'
        },
        {
            'user_id': 1,
            'session_id': 'test-session-123',
            'agent_type': 'dashboard',
            'context_data': '{"screen": "dashboard"}',
            'role': 'assistant',
            'content': 'Привет! Вот доступные треки: Основы Python, Машинное обучение, Веб-разработка'
        },
        {
            'user_id': 1,
            'session_id': 'course-session-456',
            'agent_type': 'course',
            'context_data': '{"course_id": 1, "lesson_id": 1}',
            'role': 'user',
            'content': 'Объясни что такое переменные в Python'
        }
    ]
    
    for msg in test_messages:
        cursor.execute("""
            INSERT INTO chat_messages 
            (user_id, session_id, agent_type, context_data, role, content)
            VALUES (%(user_id)s, %(session_id)s, %(agent_type)s, 
                    %(context_data)s::jsonb, %(role)s, %(content)s)
        """, msg)
    
    conn.commit()
    
    # Получение истории чата
    cursor.execute("""
        SELECT session_id, agent_type, role, content, created_at,
               context_data
        FROM chat_messages
        ORDER BY created_at
    """)
    messages = cursor.fetchall()
    
    print(f"  Добавлено и найдено сообщений: {len(messages)}")
    for msg in messages:
        print(f"    • [{msg['session_id']}] {msg['agent_type']} - "
              f"{msg['role']}: {msg['content'][:50]}...")
    
    cursor.close()
    conn.close()


def test_user_progress():
    """Тестирование прогресса пользователя"""
    print("\n🔍 Тестирование user_progress...")
    
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Добавляем прогресс для тестового пользователя
    test_progress = [
        {'user_id': 1, 'lesson_id': 1, 'is_completed': True, 'completion_percentage': 100, 'time_spent_minutes': 35},
        {'user_id': 1, 'lesson_id': 2, 'is_completed': False, 'completion_percentage': 60, 'time_spent_minutes': 25},
        {'user_id': 1, 'lesson_id': 3, 'is_completed': False, 'completion_percentage': 0, 'time_spent_minutes': 0}
    ]
    
    for progress in test_progress:
        cursor.execute("""
            INSERT INTO user_progress 
            (user_id, lesson_id, is_completed, completion_percentage, time_spent_minutes)
            VALUES (%(user_id)s, %(lesson_id)s, %(is_completed)s, 
                    %(completion_percentage)s, %(time_spent_minutes)s)
            ON CONFLICT (user_id, lesson_id) DO UPDATE SET
                is_completed = EXCLUDED.is_completed,
                completion_percentage = EXCLUDED.completion_percentage,
                time_spent_minutes = EXCLUDED.time_spent_minutes
        """, progress)
    
    conn.commit()
    
    # Получение прогресса с информацией об уроках
    cursor.execute("""
        SELECT 
            up.completion_percentage,
            up.is_completed,
            up.time_spent_minutes,
            l.title as lesson_title,
            m.title as module_title,
            t.title as track_title
        FROM user_progress up
        JOIN lessons l ON up.lesson_id = l.id
        JOIN modules m ON l.module_id = m.id
        JOIN tracks t ON m.track_id = t.id
        WHERE up.user_id = 1
        ORDER BY t.id, m.order_index, l.order_index
    """)
    progress_data = cursor.fetchall()
    
    print(f"  Найдено записей прогресса: {len(progress_data)}")
    for progress in progress_data:
        status = "✅ Завершен" if progress['is_completed'] else f"⏳ {progress['completion_percentage']}%"
        print(f"    • {progress['track_title']} → {progress['lesson_title']}: "
              f"{status} ({progress['time_spent_minutes']}мин)")
    
    cursor.close()
    conn.close()


def main():
    """Главная функция тестирования"""
    print("🧪 Тестирование работы с данными AI Learning Platform")
    print("=" * 60)
    
    try:
        test_users_table()
        test_tracks_and_modules()
        test_lessons()
        test_chat_functionality()
        test_user_progress()
        
        print("\n🎉 Все тесты прошли успешно!")
        print("✅ База данных готова к разработке")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        return False
    
    return True


if __name__ == "__main__":
    main() 