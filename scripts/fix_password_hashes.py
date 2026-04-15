#!/usr/bin/env python3
"""
Fix invalid password hashes in the database.

This script identifies users with invalid password hashes (that can't be verified by passlib)
and allows resetting their passwords.
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import database_service, User
from app.utils.security import hash_password
from sqlalchemy import select, update
from loguru import logger

async def fix_invalid_password_hashes():
    """Find and fix users with invalid password hashes."""
    print("🔧 Checking for invalid password hashes...")

    # Initialize database
    try:
        await database_service.initialize()
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")

    # Check if database is available
    if not database_service.is_database_available():
        print("❌ Database not available")
        return False

    try:
        async for session in database_service.get_session():
            # Get all users
            result = await session.execute(select(User))
            users = result.scalars().all()

            invalid_users = []

            for user in users:
                # Check if hash is valid format:
                # - bcrypt format (starts with $2)
                # - fallback format (starts with fallback$) - used when bcrypt has issues
                if not user.hashed_password or (not user.hashed_password.startswith('$2') and not user.hashed_password.startswith('fallback$')):
                    invalid_users.append(user)
                    print(f"❌ Invalid hash for user: {user.username} ({user.email})")
                    print(f"   Hash: {user.hashed_password[:30] if user.hashed_password else 'None'}...")

            if not invalid_users:
                print("✅ No users with invalid password hashes found")
                return True

            print(f"\n⚠️  Found {len(invalid_users)} users with invalid password hashes")
            print("These users will not be able to log in until their passwords are reset.")

            # For each invalid user, reset their password to a known value
            # In production, you'd want to send password reset emails instead
            for user in invalid_users:
                print(f"\n🔧 Fixing password for user: {user.username}")

                # Generate a temporary password
                temp_password = f"TempPass123!_{user.id}"

                # Hash the new password
                new_hash = hash_password(temp_password)

                # Update the user
                await session.execute(
                    update(User)
                    .where(User.id == user.id)
                    .values(hashed_password=new_hash)
                )

                print(f"✅ Password reset for {user.username}")
                print(f"   New temporary password: {temp_password}")
                print("   Please change this password after logging in!")

            await session.commit()
            print("\n✅ All invalid password hashes have been fixed")
            print("Users can now log in with their temporary passwords")

            return True

    except Exception as e:
        print(f"❌ Error fixing password hashes: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(fix_invalid_password_hashes())
    sys.exit(0 if success else 1)