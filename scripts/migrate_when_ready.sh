#!/bin/bash
# Run this script once Supabase project is restored and connection works

echo "🔍 Testing database connection before migration..."
echo ""

source venv/bin/activate

# Test connection first
python scripts/test_db_connection.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Connection successful! Proceeding with migrations..."
    echo ""
    
    # Create migration
    echo "Creating initial migration..."
    alembic revision --autogenerate -m "Initial schema"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Migration created! Applying to database..."
        echo ""
        
        # Apply migration
        alembic upgrade head
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "🎉 Database migrations completed successfully!"
        else
            echo ""
            echo "❌ Migration application failed"
        fi
    else
        echo ""
        echo "❌ Migration creation failed"
    fi
else
    echo ""
    echo "❌ Database connection failed"
    echo "Make sure your Supabase project is restored in the dashboard"
fi

