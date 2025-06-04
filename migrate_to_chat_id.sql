-- Миграция для добавления поддержки chat_id
-- Выполните этот скрипт для обновления существующей базы данных

-- Подключение к базе данных
\c ai_learning_platform;

BEGIN;

-- Создаем таблицу chats
CREATE TABLE IF NOT EXISTS chats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    chat_name VARCHAR(255),
    chat_type VARCHAR(50) DEFAULT 'planning',
    status VARCHAR(20) DEFAULT 'active',
    ai_context JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Создаем индексы для chats
CREATE INDEX IF NOT EXISTS idx_chats_session_id ON chats(session_id);
CREATE INDEX IF NOT EXISTS idx_chats_status ON chats(status);
CREATE INDEX IF NOT EXISTS idx_chats_type ON chats(chat_type);

-- Проверяем нужна ли миграция chat_messages
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='chat_messages' AND column_name='session_id'
    ) THEN
        RAISE NOTICE 'Starting migration of chat_messages to use chat_id...';
        
        -- Создаем чаты для каждой существующей сессии
        INSERT INTO chats (session_id, chat_name, chat_type, status, created_at, updated_at)
        SELECT DISTINCT 
            session_id, 
            'Main Chat',
            'planning',
            'active',
            MIN(timestamp),
            MAX(timestamp)
        FROM chat_messages
        GROUP BY session_id
        ON CONFLICT (session_id) DO NOTHING;  -- Игнорируем если чат уже существует
        
        -- Создаем новую таблицу chat_messages с правильной структурой
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
        
        -- Переносим данные из старой таблицы
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
            NULL as tokens_used,  -- Старые записи не содержат информацию о токенах
            cm.timestamp
        FROM chat_messages cm
        JOIN chats c ON c.session_id = cm.session_id
        WHERE c.chat_name = 'Main Chat';
        
        -- Удаляем старую таблицу
        DROP TABLE chat_messages;
        
        -- Переименовываем новую таблицу
        ALTER TABLE chat_messages_new RENAME TO chat_messages;
        
        -- Создаем индексы
        CREATE INDEX idx_chat_messages_chat_id ON chat_messages(chat_id);
        CREATE INDEX idx_chat_messages_timestamp ON chat_messages(timestamp);
        CREATE INDEX idx_chat_messages_sender_type ON chat_messages(sender_type);
        
        RAISE NOTICE 'Migration completed successfully!';
        
    ELSE
        -- Если таблица уже имеет правильную структуру
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='chat_messages' AND column_name='tokens_used'
        ) THEN
            -- Добавляем колонку tokens_used если её нет
            ALTER TABLE chat_messages ADD COLUMN tokens_used INTEGER;
            RAISE NOTICE 'Added tokens_used column to chat_messages';
        END IF;
        
        RAISE NOTICE 'Chat messages table already has correct structure';
    END IF;
END $$;

-- Обновляем права доступа
GRANT ALL PRIVILEGES ON TABLE chats TO "user";
GRANT ALL PRIVILEGES ON TABLE chat_messages TO "user";

COMMIT;

RAISE NOTICE 'Migration to chat_id completed successfully!'; 