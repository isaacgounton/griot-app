#!/usr/bin/env python3
"""
Reset users script to clear all users from the database.
This allows creating fresh users on next deployment.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def reset_users():
    """Reset all users in the database."""
    try:
        print("🔄 Checking if users need to be reset...")

        # Import database service
        from app.database import database_service

        # Initialize database connection
        print("📡 Connecting to database...")
        await database_service.initialize()

        # Check if there are any users
        user_count = 0
        async for session in database_service.get_session():
            try:
                from sqlalchemy import text
                result = await session.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()
                print(f"📊 Found {user_count} existing users")
                break
            except Exception as e:
                print(f"❌ Error checking users table: {e}")
                break

        if user_count == 0:
            print("✅ No users found - skipping reset")
            await database_service.close()
            return True

        # Truncate users table
        print("🗑️ Clearing users table...")
        async for session in database_service.get_session():
            try:
                from sqlalchemy import text
                await session.execute(text("TRUNCATE TABLE users CASCADE;"))
                await session.commit()
                print("✅ Users table cleared")
                break
            except Exception as e:
                print(f"❌ Error clearing users table: {e}")
                await session.rollback()
                break

        # Close database connection
        await database_service.close()

        print("🎉 Users reset completed!")
        return True

    except Exception as e:
        print(f"❌ Users reset failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(reset_users())
    sys.exit(0 if success else 1)