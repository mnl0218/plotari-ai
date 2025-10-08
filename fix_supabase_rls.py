#!/usr/bin/env python3
"""
Script to fix Supabase RLS policies for chatbot backend
"""
import os
import sys
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_rls_policies():
    """Fix RLS policies to allow anonymous access"""
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
        return False
    
    try:
        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)
        print("Connected to Supabase")
        
        # SQL to fix RLS policies
        fix_sql = """
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
        """
        
        # Execute the SQL
        result = supabase.rpc('exec_sql', {'sql': fix_sql}).execute()
        
        if result.data:
            print("RLS policies updated successfully")
            print("Anonymous access is now allowed for chatbot operations")
            return True
        else:
            print("Failed to update RLS policies")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        print("\nManual fix required:")
        print("1. Go to your Supabase dashboard")
        print("2. Navigate to Authentication > Policies")
        print("3. For 'chatbot_conversations' table:")
        print("   - Delete existing policies")
        print("   - Create new policy: 'Allow all operations' with 'true' condition")
        print("4. Repeat for 'chatbot_search_logs' table")
        return False

def test_connection():
    """Test if the chatbot can now create conversations"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        
        # Test creating a conversation
        test_conversation = {
            "user_id": "test_user_123",
            "session_id": "test_session_456",
            "conversation_data": {
                "user_id": "test_user_123",
                "session_id": "test_session_456",
                "created_at": "2024-01-01T00:00:00Z",
                "last_activity": "2024-01-01T00:00:00Z",
                "messages": [],
                "context": {}
            },
            "context": {},
            "expires_at": "2024-01-02T00:00:00Z"
        }
        
        result = supabase.table("chatbot_conversations").insert(test_conversation).execute()
        
        if result.data:
            print("Test conversation created successfully")
            
            # Clean up test data
            supabase.table("chatbot_conversations").delete().eq("user_id", "test_user_123").execute()
            print("Test data cleaned up")
            return True
        else:
            print("Failed to create test conversation")
            return False
            
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    print("Fixing Supabase RLS policies for chatbot backend...")
    print("=" * 60)
    
    # Check if we should run the fix
    if len(sys.argv) > 1 and sys.argv[1] == "--test-only":
        print("Testing connection only...")
        success = test_connection()
    else:
        print("Applying RLS policy fixes...")
        success = fix_rls_policies()
        
        if success:
            print("\nTesting the fix...")
            test_success = test_connection()
            success = success and test_success
    
    print("=" * 60)
    if success:
        print("All done! Your chatbot should now work with Supabase.")
        print("\nNext steps:")
        print("1. Restart your chatbot backend")
        print("2. Test the /api/chat endpoint")
        print("3. Check the logs for any remaining errors")
    else:
        print("Fix failed. Please check the error messages above.")
        print("\nAlternative solutions:")
        print("1. Use the service role key instead of anon key")
        print("2. Manually update policies in Supabase dashboard")
        print("3. Disable RLS entirely for development")
    
    sys.exit(0 if success else 1)
