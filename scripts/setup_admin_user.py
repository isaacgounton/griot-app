#!/usr/bin/env python3
"""
Admin Setup Script for Griot

This script creates the initial admin user for the system.
Run this script to set up your first admin user.

Usage:
    python scripts/setup_admin.py

Requirements:
    - Database must be running and accessible
    - Environment variables must be set (DATABASE_URL, etc.)
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

from app.database import database_service, User, UserRole
from app.utils.security import hash_password
from sqlalchemy import select
from loguru import logger

async def setup_admin():
    """Create the initial admin user."""

    print("🚀 Griot Admin Setup")
    print("=" * 50)

    # Check if database is available
    if not database_service.is_database_available():
        print("❌ Database is not available. Please check your DATABASE_URL and ensure the database is running.")
        return False

    try:
        async for session in database_service.get_session():
            # Check if any admin users already exist
            admin_count_result = await session.execute(
                select(User).where(User.role == UserRole.ADMIN)
            )
            existing_admins = admin_count_result.scalars().all()

            if existing_admins:
                print("⚠️  Admin user already exists!")
                for admin in existing_admins:
                    print(f"   - {admin.username} ({admin.email})")
                print("\nIf you need to create another admin, use the web interface or database directly.")
                return False

            # Get admin details from user input
            print("\n📝 Please provide admin user details:")
            print("-" * 40)

            # Get username
            while True:
                username = input("Username: ").strip()
                if not username:
                    print("❌ Username cannot be empty.")
                    continue
                if len(username) < 3:
                    print("❌ Username must be at least 3 characters.")
                    continue

                # Check if username already exists
                existing_user = await session.execute(
                    select(User).where(User.username == username)
                )
                if existing_user.scalars().first():
                    print(f"❌ Username '{username}' already exists.")
                    continue

                break

            # Get email
            while True:
                email = input("Email: ").strip()
                if not email or "@" not in email:
                    print("❌ Please enter a valid email address.")
                    continue

                # Check if email already exists
                existing_user = await session.execute(
                    select(User).where(User.email == email)
                )
                if existing_user.scalars().first():
                    print(f"❌ Email '{email}' already exists.")
                    continue

                break

            # Get full name
            while True:
                full_name = input("Full Name: ").strip()
                if not full_name:
                    print("❌ Full name cannot be empty.")
                    continue
                break

            # Get password
            while True:
                password = input("Password: ")
                if len(password) < 8:
                    print("❌ Password must be at least 8 characters.")
                    continue

                confirm_password = input("Confirm Password: ")
                if password != confirm_password:
                    print("❌ Passwords do not match.")
                    continue

                break

            print("\n🔧 Creating admin user...")

            # Create admin user
            new_admin = User(
                username=username,
                email=email,
                full_name=full_name,
                hashed_password=hash_password(password),
                role=UserRole.ADMIN,
                is_verified=True,  # Admin is pre-verified
                is_active=True
            )

            # Add and commit to database
            session.add(new_admin)
            await session.commit()
            await session.refresh(new_admin)

            print("✅ Admin user created successfully!")
            print("-" * 40)
            print(f"Username: {username}")
            print(f"Email: {email}")
            print(f"Role: {new_admin.role.value}")
            print(f"Status: {'Active' if new_admin.is_active else 'Inactive'}")
            print(f"Verified: {'Yes' if new_admin.is_verified else 'No'}")
            print()
            print("🎉 You can now log in to the admin panel!")
            print("   Go to: http://localhost:3000/admin/login")
            print("   Or use: http://localhost:3000/login (then admin features will be available)")

            return True

    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user.")
        return False
    except Exception as e:
        logger.error(f"❌ Error during admin setup: {str(e)}")
        print(f"❌ Error during admin setup: {str(e)}")
        return False

async def main():
    """Main entry point."""
    try:
        success = await setup_admin()
        if success:
            print("\n🎊 Admin setup completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Admin setup failed or was cancelled.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())