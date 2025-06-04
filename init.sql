-- Инициализация базы данных AI Learning Platform
-- Этот файл выполняется при первом запуске PostgreSQL контейнера

-- Создание базы данных (уже создается через POSTGRES_DB)
-- CREATE DATABASE ai_learning_platform;

-- Создание пользователя (уже создается через POSTGRES_USER/POSTGRES_PASSWORD)
-- CREATE USER user WITH PASSWORD 'password';

-- Предоставление прав
GRANT ALL PRIVILEGES ON DATABASE ai_learning_platform TO "user";

-- Подключение к базе данных
\c ai_learning_platform;

-- Создание расширения для UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Создание расширения для криптографии (если понадобится)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Предоставление прав на схему public
GRANT ALL ON SCHEMA public TO "user";
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "user";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "user";

-- Установка владельца схемы
ALTER SCHEMA public OWNER TO "user";

-- Миграция: добавление таблицы chats и обновление chat_messages для поддержки chat_id
-- Данный скрипт выполнится автоматически при пересоздании БД

-- Если таблица chat_messages уже существует, нужно выполнить миграцию
DO $$
BEGIN
    -- Проверяем существует ли таблица chat_messages с старой структурой
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='chat_messages' AND column_name='session_id'
    ) THEN
        -- Создаем таблицу chats если её нет
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='chats') THEN
            CREATE TABLE chats (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
                chat_name VARCHAR(255),
                chat_type VARCHAR(50) DEFAULT 'planning',
                status VARCHAR(20) DEFAULT 'active',
                ai_context JSONB,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            
            CREATE INDEX idx_chats_session_id ON chats(session_id);
            CREATE INDEX idx_chats_status ON chats(status);
        END IF;
        
        -- Создаем временную таблицу для новых сообщений
        CREATE TABLE chat_messages_new (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            chat_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
            sender_type VARCHAR(10) NOT NULL,
            message_content TEXT NOT NULL,
            message_type VARCHAR(20) DEFAULT 'text',
            ai_model_used VARCHAR(100),
            tokens_used INTEGER,
            timestamp TIMESTAMP DEFAULT NOW()
        );
        
        -- Мигрируем данные: создаем чаты для каждой сессии и переносим сообщения
        INSERT INTO chats (session_id, chat_name, chat_type, status, created_at, updated_at)
        SELECT DISTINCT 
            session_id, 
            'Migrated Chat',
            'planning',
            'active',
            MIN(timestamp),
            MAX(timestamp)
        FROM chat_messages
        GROUP BY session_id;
        
        -- Переносим сообщения в новую таблицу
        INSERT INTO chat_messages_new (
            chat_id, sender_type, message_content, message_type, 
            ai_model_used, tokens_used, timestamp
        )
        SELECT 
            c.id as chat_id,
            cm.sender_type,
            cm.message_content,
            cm.message_type,
            cm.ai_model_used,
            NULL as tokens_used,  -- Старые сообщения не имеют информации о токенах
            cm.timestamp
        FROM chat_messages cm
        JOIN chats c ON c.session_id = cm.session_id
        WHERE c.chat_name = 'Migrated Chat';
        
        -- Удаляем старую таблицу и переименовываем новую
        DROP TABLE chat_messages;
        ALTER TABLE chat_messages_new RENAME TO chat_messages;
        
        -- Создаем индексы для новой таблицы
        CREATE INDEX idx_chat_messages_chat_id ON chat_messages(chat_id);
        CREATE INDEX idx_chat_messages_timestamp ON chat_messages(timestamp);
        CREATE INDEX idx_chat_messages_sender_type ON chat_messages(sender_type);
        
        RAISE NOTICE 'Migration completed: chat_messages migrated to use chat_id';
    END IF;
END $$; 