#!/usr/bin/env python3
"""
Migration script to add stripe and subscription columns to the users table if they are missing.
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env
load_dotenv()

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def migrate_subscription_columns():
    try:
        print("🔧 Running subscription column migration...")
        from app.database import database_service
        await database_service.initialize()

        if not database_service.is_database_available():
            print("❌ Database not available")
            return False

        if not database_service.engine:
            print("❌ Database engine not initialized")
            return False

        async with database_service.engine.begin() as conn:
            from sqlalchemy import text

            checks = [
                ("stripe_customer_id", "VARCHAR(255)"),
                ("stripe_subscription_id", "VARCHAR(255)"),
                ("subscription_status", "VARCHAR(50)"),
                ("subscription_expires_at", "TIMESTAMP"),
            ]

            for column_name, column_type in checks:
                result = await conn.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'users' AND column_name = :col
                    )
                """), {"col": column_name})
                exists = result.scalar()

                if exists:
                    print(f"✅ Column {column_name} already exists")
                else:
                    print(f"📝 Adding {column_name} to users table...")
                    await conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"))
                    print(f"✅ Added {column_name}")

        await database_service.close()
        print("🎉 Subscription columns migration completed")
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    success = await migrate_subscription_columns()
    return 0 if success else 1

if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
