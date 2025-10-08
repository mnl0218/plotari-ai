"""
Application configuration
"""
import os
from dotenv import load_dotenv
from typing import Optional
from supabase import create_client

# Load environment variables
load_dotenv()

class Settings:
    """Application configuration"""
    
    # Weaviate
    WEAVIATE_URL: str = os.getenv("WEAVIATE_URL", "")
    WEAVIATE_API_KEY: str = os.getenv("WEAVIATE_API_KEY", "")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    
    # Application
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Supabase client
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
    
    @classmethod
    def validate(cls) -> bool:
        """Validates that all required environment variables are present"""
        required_vars = [
            "WEAVIATE_URL",
            "WEAVIATE_API_KEY", 
            "OPENAI_API_KEY",
            "SUPABASE_URL",
            "SUPABASE_ANON_KEY"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing the following environment variables: {', '.join(missing_vars)}")
        
        return True

# Global configuration instance
settings = Settings()