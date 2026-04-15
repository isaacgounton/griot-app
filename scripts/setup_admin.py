#!/usr/bin/env python3
"""
Setup script to create default admin user and API key for testing.
This removes all mock data and creates real database entries.
"""
import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta

# Add the app directory to the Python path
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from app.database import database_service
from app.services.user_service import user_service
from app.services.api_key_service import api_key_service

async def setup_admin():
    """Create default admin user and API key."""
    try:
        # Initialize database
        await database_service.initialize()
        await database_service.create_tables()
        await database_service.update_enums()
        
        print("✅ Database initialized successfully")
        
        # Get credentials from environment variables (required for production)
        admin_password = os.getenv("ADMIN_PASSWORD")
        if not admin_password:
            print("❌ ADMIN_PASSWORD environment variable is required")
            return False
        
        # Create admin user
        admin_data = {
            "username": "admin",
            "email": "admin@griot.com", 
            "full_name": "Administrator",
            "password": admin_password,
            "role": "admin",
            "is_active": True
        }
        
        try:
            # Check if admin user already exists
            existing_user = await user_service.get_user_by_email(admin_data["email"])
            if existing_user:
                print(f"✅ Admin user already exists: {existing_user['email']}")
                user_id = int(existing_user["id"])
            else:
                # Create new admin user
                user_result = await user_service.create_user(admin_data)
                user_id = int(user_result["id"])
                print(f"✅ Created admin user: {user_result['email']}")
        except Exception as e:
            print(f"❌ Failed to create admin user: {e}")
            return False
        
        # Create default API key
        api_key_data = {
            "name": "Admin API Key",
            "user_id": str(user_id),
            "rate_limit": 1000,
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=365)).replace(tzinfo=None),
            "is_active": True
        }
        
        try:
            # Check existing API keys for this user
            existing_keys = await api_key_service.list_api_keys(user_id=user_id)
            if existing_keys["api_keys"]:
                print(f"✅ Admin user already has {len(existing_keys['api_keys'])} API key(s)")
                for key in existing_keys["api_keys"]:
                    print(f"   - {key['name']}: {key['key']}")
            else:
                # Create new API key
                key_result = await api_key_service.create_api_key(api_key_data)
                print(f"✅ Created API key: {key_result['name']}")
                print(f"   API Key: {key_result['key']}")
                print(f"   Key ID: {key_result['key_id']}")
        except Exception as e:
            print(f"❌ Failed to create API key: {e}")
            return False
        
        print("\n🎉 Setup completed successfully!")
        print("\nYou can now:")
        print("1. Access the admin dashboard at: http://localhost:8000/dashboard")
        print("2. Login with: admin@griot.com / (password from ADMIN_PASSWORD env var)") 
        print("3. Use the API key shown above for authentication")
        print("\n📋 Required environment variables:")
        print("   ADMIN_USERNAME=admin")
        print("   ADMIN_PASSWORD=<your_secure_password>")
        print("   API_KEY=<your_api_key>")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await database_service.close()

if __name__ == "__main__":
    print("🚀 Setting up admin user and API key...")
    success = asyncio.run(setup_admin())
    sys.exit(0 if success else 1)