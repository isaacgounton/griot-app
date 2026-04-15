#!/usr/bin/env python3
"""
Database initialization script to ensure video library persistence.
This script creates the necessary database tables when run.
Designed to run automatically during application startup.
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path (go up one level from scripts/)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def init_database():
    """Initialize the database with all required tables."""
    try:
        print("🔧 Initializing Griot database...")
        
        # Import database service
        from app.database import database_service
        
        # Initialize database connection
        print("📡 Connecting to database...")
        await database_service.initialize()
        
        # Create all tables
        print("🏗️ Creating database tables...")
        await database_service.create_tables()
        
        print("✅ Database initialization completed!")
        
        # Run schema migrations to add missing columns and enums
        print("🔧 Running database migrations (migrate_schema)")
        await database_service.migrate_schema()

        # Verify tables were created
        print("🔍 Verifying table creation...")
        
        # Test database connection by querying a simple table
        async for session in database_service.get_session():
            try:
                from sqlalchemy import text
                result = await session.execute(text("SELECT COUNT(*) FROM videos"))
                count = result.scalar()
                print(f"📊 Videos table exists and contains {count} records")
                
                result = await session.execute(text("SELECT COUNT(*) FROM jobs"))
                count = result.scalar()
                print(f"📊 Jobs table exists and contains {count} records")
                
                result = await session.execute(text("SELECT COUNT(*) FROM users"))
                count = result.scalar()
                print(f"📊 Users table exists and contains {count} records")
                
                break
                
            except Exception as e:
                print(f"⚠️ Error verifying tables: {e}")
                break
        
        # Close database connection
        await database_service.close()
        
        print("\n🎉 Database is ready for video library persistence!")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_video_service():
    """Test the video service to ensure it works properly."""
    try:
        print("\n🧪 Testing video service...")
        
        from app.services.video.video_service import video_service
        from app.database import VideoType
        
        # Test getting all videos
        videos = await video_service.get_all_videos(limit=5)
        print(f"📼 Found {len(videos)} existing videos in library")
        
        # Test getting video stats
        stats = await video_service.get_video_stats()
        print(f"📊 Video statistics: {stats}")
        
        print("✅ Video service is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Video service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_environment():
    """Check if all required environment variables are set."""
    print("🔍 Checking environment configuration...")
    
    required_vars = [
        'DATABASE_URL',
        'POSTGRES_PASSWORD',
        'S3_ACCESS_KEY',
        'S3_SECRET_KEY',
        'S3_BUCKET_NAME'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️ Missing environment variables: {missing_vars}")
        print("💡 Make sure to set these in your .env file or environment")
        return False
    else:
        print("✅ All required environment variables are set")
        
        # Keep original DATABASE_URL for container deployment
        
        return True

async def main():
    """Main function to run all initialization steps."""
    print("🚀 Griot Database Initialization Script")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Please configure required variables.")
        return False
    
    # Initialize database
    db_success = await init_database()
    if not db_success:
        print("\n❌ Database initialization failed.")
        return False
    
    # Test video service (non-critical)
    video_success = await test_video_service()
    if not video_success:
        print("\n⚠️ Video service test failed (non-critical, continuing initialization).")
    
    print("\n" + "=" * 50)
    print("🎉 SUCCESS! Your video library should now persist across redeploys!")
    print("💡 Tips for maintaining persistence:")
    print("   • Always use 'docker-compose up' instead of 'docker-compose up --build' when possible")
    print("   • The postgres_data and redis_data volumes contain your persistent data")
    print("   • Videos are stored in S3 and metadata in PostgreSQL")
    print("   • Check /dashboard/library to see your video library")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)