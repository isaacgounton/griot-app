#!/bin/bash

# Initialize database tables for Griot
# This script creates the PostgreSQL database tables if they don't exist

set -e

echo "🗄️  Initializing Griot Database..."
echo ""

# Load environment variables
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
else
    echo "❌ .env file not found"
    exit 1
fi

# Check Python environment
if ! command -v python &> /dev/null; then
    echo "❌ Python not found"
    exit 1
fi

echo "📝 Creating database tables..."
echo ""

# Run Python script to create tables using UV
uv run python -c "
import asyncio
import sys
from app.database import database_service

async def init_db():
    try:
        # Initialize database connection
        await database_service.initialize()
        
        if not database_service.is_database_available():
            print('❌ Database not available')
            sys.exit(1)
        
        # Create tables
        await database_service.create_tables()
        print('✅ Database tables created successfully')
        
        # Update enums
        await database_service.update_enums()
        print('✅ Database enums updated successfully')
        
        # Migrate schema (add missing columns)
        await database_service.migrate_schema()
        print('✅ Database schema migrated successfully')
        
        # Close connection
        await database_service.close()
        
    except Exception as e:
        print(f'❌ Error initializing database: {e}')
        sys.exit(1)

asyncio.run(init_db())
"

echo ""
echo "🎉 Database initialization complete!"
echo ""
echo "You can now:"
echo "  1. Register a new user at http://localhost:5173/register"
echo "  2. Verify your email"
echo "  3. Log in with your credentials at http://localhost:5173/login"
