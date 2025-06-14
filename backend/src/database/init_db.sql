-- AI Learning Platform Database Schema
-- Создание базовой структуры БД для платформы обучения

-- Удаление существующих таблиц если они есть
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS user_progress CASCADE;
DROP TABLE IF EXISTS lessons CASCADE;
DROP TABLE IF EXISTS modules CASCADE;
DROP TABLE IF EXISTS tracks CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Создание enum типов
CREATE TYPE user_role AS ENUM ('user', 'admin', 'instructor');
CREATE TYPE ai_personality AS ENUM ('friendly', 'professional', 'casual', 'motivating');
CREATE TYPE message_role AS ENUM ('user', 'assistant', 'system');
CREATE TYPE lesson_type AS ENUM ('theory', 'practice', 'quiz', 'project');

-- Таблица пользователей
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role user_role DEFAULT 'user',
    ai_personality ai_personality DEFAULT 'friendly',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Таблица треков (курсов)
CREATE TABLE tracks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    image_url VARCHAR(500),
    difficulty_level INTEGER DEFAULT 1 CHECK (difficulty_level >= 1 AND difficulty_level <= 5),
    estimated_duration_hours INTEGER,
    is_published BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица модулей
CREATE TABLE modules (
    id SERIAL PRIMARY KEY,
    track_id INTEGER REFERENCES tracks(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица уроков
CREATE TABLE lessons (
    id SERIAL PRIMARY KEY,
    module_id INTEGER REFERENCES modules(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    lesson_type lesson_type DEFAULT 'theory',
    order_index INTEGER NOT NULL,
    estimated_minutes INTEGER,
    is_published BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Таблица прогресса пользователей
CREATE TABLE user_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    lesson_id INTEGER REFERENCES lessons(id) ON DELETE CASCADE,
    is_completed BOOLEAN DEFAULT false,
    completion_percentage INTEGER DEFAULT 0 CHECK (completion_percentage >= 0 AND completion_percentage <= 100),
    time_spent_minutes INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, lesson_id)
);

-- Таблица сообщений чата
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    agent_type VARCHAR(50) NOT NULL, -- 'dashboard', 'course', etc.
    context_data JSONB, -- { "course_id": 123, "lesson_id": 456 }
    role message_role NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB, -- дополнительные данные: токены, модель и т.д.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создание индексов для оптимизации запросов
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_modules_track_order ON modules(track_id, order_index);
CREATE INDEX idx_lessons_module_order ON lessons(module_id, order_index);
CREATE INDEX idx_user_progress_user_lesson ON user_progress(user_id, lesson_id);
CREATE INDEX idx_chat_messages_user_session ON chat_messages(user_id, session_id);
CREATE INDEX idx_chat_messages_agent_context ON chat_messages(agent_type, context_data);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры для автоматического обновления updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tracks_updated_at BEFORE UPDATE ON tracks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Вставка тестовых данных
INSERT INTO tracks (title, description, difficulty_level, estimated_duration_hours, is_published) VALUES
('Основы Python', 'Изучение основ программирования на Python', 1, 40, true),
('Машинное обучение', 'Введение в машинное обучение и нейронные сети', 3, 60, true),
('Веб-разработка', 'Создание веб-приложений с использованием современных технологий', 2, 50, true);

INSERT INTO modules (track_id, title, description, order_index) VALUES
(1, 'Введение в Python', 'Основы синтаксиса и структуры данных', 1),
(1, 'Функции и классы', 'Объектно-ориентированное программирование', 2),
(2, 'Основы ML', 'Теория машинного обучения', 1),
(2, 'Практика ML', 'Реализация алгоритмов', 2);

INSERT INTO lessons (module_id, title, content, lesson_type, order_index, estimated_minutes, is_published) VALUES
(1, 'Переменные и типы данных', 'Изучение базовых типов данных в Python', 'theory', 1, 30, true),
(1, 'Практика: работа с переменными', 'Практические задания по переменным', 'practice', 2, 45, true),
(2, 'Функции в Python', 'Создание и использование функций', 'theory', 1, 40, true),
(3, 'Что такое машинное обучение?', 'Введение в концепции ML', 'theory', 1, 35, true);

-- Создание тестового пользователя (пароль: test123)
INSERT INTO users (email, password_hash, first_name, last_name, ai_personality) VALUES
('test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LedhZWBdmjsD1BQ/6', 'Тест', 'Пользователь', 'friendly');

COMMIT; 