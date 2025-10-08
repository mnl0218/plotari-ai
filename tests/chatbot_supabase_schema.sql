-- =====================================================
-- ESQUEMA SIMPLIFICADO DE BASE DE DATOS PARA CHATBOT - SUPABASE
-- =====================================================

-- Habilitar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =====================================================
-- TABLA PRINCIPAL DE CONVERSACIONES (REEMPLAZA CACHE Y SESIONES)
-- =====================================================
CREATE TABLE chatbot_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL, -- ID del usuario de Supabase Auth
    session_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    conversation_data JSONB NOT NULL, -- Almacena toda la conversación como en el cache
    context JSONB DEFAULT '{}', -- Contexto de la conversación
    chat_summary TEXT, -- Resumen de la conversación
    expires_at TIMESTAMP WITH TIME ZONE, -- Para limpieza automática
    UNIQUE(user_id, session_id)
);

-- =====================================================
-- TABLA DE BÚSQUEDAS Y RESULTADOS (OPTIONAL - PARA ANALYTICS)
-- =====================================================
CREATE TABLE chatbot_search_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES chatbot_conversations(id) ON DELETE CASCADE,
    search_type VARCHAR(50) NOT NULL CHECK (search_type IN ('property_search', 'poi_search', 'general_inquiry')),
    query TEXT NOT NULL,
    filters JSONB DEFAULT '{}',
    results_count INTEGER DEFAULT 0,
    search_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    response_time_ms INTEGER,
    metadata JSONB DEFAULT '{}'
);

-- =====================================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- =====================================================

-- Índices para chatbot_conversations
CREATE INDEX idx_chatbot_conversations_user_id ON chatbot_conversations(user_id);
CREATE INDEX idx_chatbot_conversations_session_id ON chatbot_conversations(session_id);
CREATE INDEX idx_chatbot_conversations_last_activity ON chatbot_conversations(last_activity);
CREATE INDEX idx_chatbot_conversations_created_at ON chatbot_conversations(created_at);
CREATE INDEX idx_chatbot_conversations_expires_at ON chatbot_conversations(expires_at);
CREATE INDEX idx_chatbot_conversations_is_active ON chatbot_conversations(is_active);

-- Índices para chatbot_search_logs
CREATE INDEX idx_chatbot_search_logs_conversation_id ON chatbot_search_logs(conversation_id);
CREATE INDEX idx_chatbot_search_logs_search_type ON chatbot_search_logs(search_type);
CREATE INDEX idx_chatbot_search_logs_search_timestamp ON chatbot_search_logs(search_timestamp);

-- Índices para búsqueda de texto completo en conversation_data
CREATE INDEX idx_chatbot_conversations_data_gin ON chatbot_conversations USING GIN (conversation_data);
CREATE INDEX idx_chatbot_search_logs_query_gin ON chatbot_search_logs USING GIN (to_tsvector('english', query));

-- =====================================================
-- FUNCIONES Y TRIGGERS
-- =====================================================

-- Función para actualizar last_activity automáticamente
CREATE OR REPLACE FUNCTION update_last_activity()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_activity = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para actualizar last_activity en conversaciones
CREATE TRIGGER update_chatbot_conversations_last_activity 
    BEFORE UPDATE ON chatbot_conversations 
    FOR EACH ROW EXECUTE FUNCTION update_last_activity();

-- Función para limpiar conversaciones expiradas
CREATE OR REPLACE FUNCTION cleanup_expired_conversations()
RETURNS void AS $$
BEGIN
    DELETE FROM chatbot_conversations 
    WHERE expires_at < NOW() AND is_active = true;
END;
$$ language 'plpgsql';

-- Función para obtener estadísticas de conversación
CREATE OR REPLACE FUNCTION get_conversation_stats(p_user_id VARCHAR, p_days INTEGER DEFAULT 30)
RETURNS TABLE (
    total_conversations BIGINT,
    total_messages BIGINT,
    avg_messages_per_conversation NUMERIC,
    last_activity TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(c.id) as total_conversations,
        COALESCE(SUM((c.conversation_data->>'messages')::jsonb), '[]'::jsonb)::jsonb #>> '{}' as total_messages,
        ROUND(
            COALESCE(SUM((c.conversation_data->>'messages')::jsonb), '[]'::jsonb)::jsonb #>> '{}'::NUMERIC / 
            NULLIF(COUNT(c.id), 0), 2
        ) as avg_messages_per_conversation,
        MAX(c.last_activity) as last_activity
    FROM chatbot_conversations c
    WHERE c.user_id = p_user_id 
    AND c.created_at >= NOW() - INTERVAL '1 day' * p_days;
END;
$$ language 'plpgsql';

-- Función para obtener conversación por usuario y sesión
CREATE OR REPLACE FUNCTION get_conversation(p_user_id VARCHAR, p_session_id VARCHAR)
RETURNS TABLE (
    conversation_data JSONB,
    context JSONB,
    last_activity TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.conversation_data,
        c.context,
        c.last_activity
    FROM chatbot_conversations c
    WHERE c.user_id = p_user_id 
    AND c.session_id = p_session_id
    AND c.is_active = true;
END;
$$ language 'plpgsql';

-- =====================================================
-- POLÍTICAS DE SEGURIDAD (RLS)
-- =====================================================

-- Habilitar RLS en las tablas
ALTER TABLE chatbot_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE chatbot_search_logs ENABLE ROW LEVEL SECURITY;

-- Políticas para chatbot_conversations
CREATE POLICY "Users can view own conversations" ON chatbot_conversations
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own conversations" ON chatbot_conversations
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own conversations" ON chatbot_conversations
    FOR UPDATE USING (auth.uid()::text = user_id);

CREATE POLICY "Users can delete own conversations" ON chatbot_conversations
    FOR DELETE USING (auth.uid()::text = user_id);

-- Políticas para chatbot_search_logs
CREATE POLICY "Users can view own search logs" ON chatbot_search_logs
    FOR SELECT USING (conversation_id IN (
        SELECT id FROM chatbot_conversations WHERE user_id = auth.uid()::text
    ));

CREATE POLICY "Users can insert own search logs" ON chatbot_search_logs
    FOR INSERT WITH CHECK (conversation_id IN (
        SELECT id FROM chatbot_conversations WHERE user_id = auth.uid()::text
    ));

-- =====================================================
-- VISTAS ÚTILES
-- =====================================================

-- Vista para resumen de conversaciones
CREATE VIEW chatbot_conversation_summary AS
SELECT 
    c.user_id,
    c.session_id,
    c.created_at,
    c.last_activity,
    c.is_active,
    jsonb_array_length(c.conversation_data->'messages') as message_count,
    c.conversation_data->'messages'->-1->>'timestamp' as last_message_time
FROM chatbot_conversations c
WHERE c.is_active = true;

-- Vista para estadísticas de búsquedas
CREATE VIEW chatbot_search_stats AS
SELECT 
    sl.search_type,
    COUNT(*) as search_count,
    AVG(sl.results_count) as avg_results_count,
    AVG(sl.response_time_ms) as avg_response_time_ms,
    COUNT(DISTINCT c.user_id) as unique_users
FROM chatbot_search_logs sl
JOIN chatbot_conversations c ON sl.conversation_id = c.id
GROUP BY sl.search_type;

-- =====================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- =====================================================

COMMENT ON TABLE chatbot_conversations IS 'Conversaciones del chatbot - almacena toda la data como JSONB';
COMMENT ON TABLE chatbot_search_logs IS 'Log de búsquedas para analytics y debugging';
COMMENT ON COLUMN chatbot_conversations.conversation_data IS 'JSONB con estructura: {user_id, session_id, created_at, last_activity, messages: [], context: {}}';
COMMENT ON COLUMN chatbot_conversations.context IS 'Contexto de la conversación: last_search_intent, user_preferences, etc.';
COMMENT ON COLUMN chatbot_conversations.expires_at IS 'Timestamp para limpieza automática de conversaciones inactivas';
