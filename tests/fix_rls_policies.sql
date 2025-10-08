-- =====================================================
-- FIX RLS POLICIES FOR CHATBOT BACKEND
-- =====================================================

-- Option 1: Disable RLS (for development/testing)
-- ALTER TABLE chatbot_conversations DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE chatbot_search_logs DISABLE ROW LEVEL SECURITY;

-- Option 2: Create policies that allow anonymous access (recommended for chatbot)
-- Drop existing policies
DROP POLICY IF EXISTS "Users can view own conversations" ON chatbot_conversations;
DROP POLICY IF EXISTS "Users can insert own conversations" ON chatbot_conversations;
DROP POLICY IF EXISTS "Users can update own conversations" ON chatbot_conversations;
DROP POLICY IF EXISTS "Users can delete own conversations" ON chatbot_conversations;

DROP POLICY IF EXISTS "Users can view own search logs" ON chatbot_search_logs;
DROP POLICY IF EXISTS "Users can insert own search logs" ON chatbot_search_logs;

-- Create new policies that allow anonymous access
CREATE POLICY "Allow anonymous access to conversations" ON chatbot_conversations
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow anonymous access to search logs" ON chatbot_search_logs
    FOR ALL USING (true) WITH CHECK (true);

-- Option 3: Create policies that check for valid user_id format (more secure)
-- Uncomment this section if you want to use this approach instead

/*
-- Drop the anonymous policies
DROP POLICY IF EXISTS "Allow anonymous access to conversations" ON chatbot_conversations;
DROP POLICY IF EXISTS "Allow anonymous access to search logs" ON chatbot_search_logs;

-- Create policies that validate user_id format
CREATE POLICY "Allow valid user_id format" ON chatbot_conversations
    FOR ALL USING (
        user_id IS NOT NULL 
        AND user_id != '' 
        AND (user_id LIKE 'user_%' OR user_id LIKE 'anon_%' OR user_id ~ '^[a-zA-Z0-9_-]+$')
    ) WITH CHECK (
        user_id IS NOT NULL 
        AND user_id != '' 
        AND (user_id LIKE 'user_%' OR user_id LIKE 'anon_%' OR user_id ~ '^[a-zA-Z0-9_-]+$')
    );

CREATE POLICY "Allow valid user_id format for search logs" ON chatbot_search_logs
    FOR ALL USING (
        conversation_id IN (
            SELECT id FROM chatbot_conversations 
            WHERE user_id IS NOT NULL 
            AND user_id != '' 
            AND (user_id LIKE 'user_%' OR user_id LIKE 'anon_%' OR user_id ~ '^[a-zA-Z0-9_-]+$')
        )
    ) WITH CHECK (
        conversation_id IN (
            SELECT id FROM chatbot_conversations 
            WHERE user_id IS NOT NULL 
            AND user_id != '' 
            AND (user_id LIKE 'user_%' OR user_id LIKE 'anon_%' OR user_id ~ '^[a-zA-Z0-9_-]+$')
        )
    );
*/

-- Verify the policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
FROM pg_policies 
WHERE tablename IN ('chatbot_conversations', 'chatbot_search_logs')
ORDER BY tablename, policyname;
