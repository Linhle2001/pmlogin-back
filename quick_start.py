#!/usr/bin/env python3
"""
Quick start script for PM Login Backend
"""
import subprocess
import sys
import os

def quick_start():
    """Quick start the PM Login Backend"""
    
    print("PM Login Backend - Quick Start")
    print("=" * 50)
    
    # Step 1: Setup demo environment
    print("Step 1: Setting up demo environment...")
    try:
        result = subprocess.run([sys.executable, "utils/setup.py"], 
                              capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print("Demo environment setup successful")
        else:
            print("Demo environment setup failed")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"Error setting up demo environment: {e}")
        return False
    
    print()
    
    # Step 2: Start the server
    print("Step 2: Starting the backend server...")
    print("Server will start on: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print()
    print("Login credentials:")
    print("   Email: lelinh21102001@gmail.com")
    print("   Password: lelinh21102001@gmail.com")
    print()
    print("Starting server... (Press Ctrl+C to stop)")
    print("=" * 50)
    
    try:
        # Start the server
        subprocess.run([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        return True
    except Exception as e:
        print(f"Error starting server: {e}")
        return False

if __name__ == "__main__":
    success = quick_start()
    if not success:
        sys.exit(1)