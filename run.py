#!/usr/bin/env python3
"""
Quick start script for the chatbot backend
"""
import sys
import os
import subprocess
from pathlib import Path

def check_requirements():
    """Checks that requirements are installed"""
    try:
        import weaviate
        import openai
        import fastapi
        import uvicorn
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Checks that the .env file exists"""
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file found")
        return True
    else:
        print("❌ .env file not found")
        print("💡 Copy env.example to .env and configure your credentials")
        return False

def run_tests():
    """Runs connection tests"""
    print("\n🧪 Running connection tests...")
    try:
        result = subprocess.run([sys.executable, "test_connection.py"], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def start_server():
    """Starts the server"""
    print("\n🚀 Starting server...")
    try:
        subprocess.run([sys.executable, "-m", "src.main"])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def main():
    """Main function"""
    print("🏠 Plotari Chatbot Backend")
    print("=" * 40)
    
    # Initial checks
    if not check_requirements():
        return
    
    if not check_env_file():
        return
    
    # Ask if running tests
    run_tests_choice = input("\nRun connection tests? (y/n): ").lower().strip()
    if run_tests_choice in ['y', 'yes']:
        if not run_tests():
            print("⚠️  Some tests failed. Continue anyway? (y/n): ", end="")
            if input().lower().strip() not in ['y', 'yes']:
                return
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
