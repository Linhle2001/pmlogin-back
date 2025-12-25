#!/usr/bin/env python3
"""
Setup utilities for PM Login Backend
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import models first
from core.models import User, Base
from core.database import get_db, init_db
from core.auth import get_password_hash
from datetime import datetime

def setup_demo_environment():
    """Setup complete demo environment"""
    
    print("Setting up PM Login Demo Environment...")
    print()
    
    # Step 1: Initialize database
    print("Initializing database...")
    try:
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        return False
    
    # Step 2: Create test user with correct HWID
    print("Creating test user...")
    db = next(get_db())
    
    # Your Hardware ID
    correct_hwid = "90f83d628bf36ed75c755fabe9b77c76b595dbe0df3912707583c2a04bb4fa05"
    
    try:
        # Check if main user already exists
        existing_user = db.query(User).filter(User.email == "lelinh21102001@gmail.com").first()
        
        if existing_user:
            # Update existing user with correct HWID
            existing_user.hwid = correct_hwid
            existing_user.last_login = datetime.utcnow()
            print("Main user updated with correct HWID!")
        else:
            # Create new main user
            main_user = User(
                email="lelinh21102001@gmail.com",
                hashed_password=get_password_hash("lelinh21102001@gmail.com"),
                hwid=correct_hwid,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(main_user)
            print("Main user created successfully!")
        
        # Create additional demo users
        demo_users = [
            {"email": "demo@pmlogin.com", "password": "demo123"},
            {"email": "test@example.com", "password": "test123"},
            {"email": "admin@pmlogin.com", "password": "admin123"},
        ]
        
        print("Creating additional demo users...")
        for user_data in demo_users:
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            
            if existing:
                # Update existing user
                existing.hwid = correct_hwid
                existing.hashed_password = get_password_hash(user_data["password"])
                existing.last_login = datetime.utcnow()
                print(f"   Updated: {user_data['email']} (password: {user_data['password']})")
            else:
                # Create new user
                new_user = User(
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    hwid=correct_hwid,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.add(new_user)
                print(f"   Created: {user_data['email']} (password: {user_data['password']})")
        
        db.commit()
        
        print()
        print("Demo environment setup completed!")
        print()
        print("Available login credentials (all with correct HWID):")
        print("   1. Email: lelinh21102001@gmail.com")
        print("      Password: lelinh21102001@gmail.com")
        print()
        print("   2. Email: demo@pmlogin.com")
        print("      Password: demo123")
        print()
        print("   3. Email: test@example.com")
        print("      Password: test123")
        print()
        print("   4. Email: admin@pmlogin.com")
        print("      Password: admin123")
        print()
        print("Next steps:")
        print("1. Start backend: python app.py")
        print("2. Start frontend: npm start (in pmlogin-app_v2)")
        print("3. Login with any of the above credentials")
        
        return True
        
    except Exception as e:
        print(f"Error setting up demo environment: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = setup_demo_environment()
    
    if not success:
        print("Demo setup failed!")
        sys.exit(1)
    else:
        print("Demo setup successful!")
        sys.exit(0)