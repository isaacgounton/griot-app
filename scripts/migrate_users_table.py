#!/usr/bin/env python3
"""
Migration script to add missing columns to the users table.
This script adds the is_verified column that was missing from the database schema.
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

async def migrate_users_table():
    """Add missing columns to the users table."""
    try:
        print("🔧 Migrating users table...")
        
        # Import database service
        from app.database import database_service
        
        # Initialize database connection
        print("📡 Connecting to database...")
        await database_service.initialize()
        
        if not database_service.is_database_available():
            print("❌ Database not available")
            return False
        
        # Check if column already exists and add it if missing
        async for session in database_service.get_session():
            try:
                from sqlalchemy import text
                
                # Check if is_verified column exists
                result = await session.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'users' 
                        AND column_name = 'is_verified'
                    )
                """))
                
                column_exists = result.scalar()
                
                if column_exists:
                    print("✅ is_verified column already exists")
                else:
                    print("📝 Adding is_verified column to users table...")
                    
                    # Add the is_verified column with default value False
                    await session.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN is_verified BOOLEAN NOT NULL DEFAULT FALSE
                    """))
                    
                    await session.commit()
                    print("✅ Successfully added is_verified column")
                
                # Check if verification_token column exists
                result = await session.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'users' 
                        AND column_name = 'verification_token'
                    )
                """))
                
                token_exists = result.scalar()
                
                if token_exists:
                    print("✅ verification_token column already exists")
                else:
                    print("📝 Adding verification_token columns to users table...")
                    
                    # Add verification token columns
                    await session.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN verification_token VARCHAR(255) UNIQUE,
                        ADD COLUMN verification_token_expires_at TIMESTAMP
                    """))
                    
                    await session.commit()
                    print("✅ Successfully added verification token columns")
                
                break
                
            except Exception as e:
                print(f"❌ Migration failed: {e}")
                await session.rollback()
                return False
        
        # Close database connection
        await database_service.close()
        
        print("✅ Users table migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main migration function."""
    print("🚀 Griot Users Table Migration Script")
    print("=" * 50)
    
    success = await migrate_users_table()
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 SUCCESS! Users table has been migrated!")
        print("💡 The following columns have been added:")
        print("   • is_verified (BOOLEAN, default FALSE)")
        print("   • verification_token (VARCHAR(255), unique)")
        print("   • verification_token_expires_at (TIMESTAMP)")
    else:
        print("\n❌ Migration failed!")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
