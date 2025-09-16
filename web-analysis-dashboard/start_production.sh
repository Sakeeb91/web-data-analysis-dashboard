#!/bin/bash

echo "==========================================="
echo "Starting Web Data Analysis Dashboard"
echo "Production Mode - Phase 1"
echo "==========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies from requirements_production.txt..."
if [ -f "requirements_production.txt" ]; then
    pip install -r requirements_production.txt
else
    echo "requirements_production.txt not found, installing minimal set..."
    pip install Flask Flask-SQLAlchemy Flask-CORS Flask-Login Flask-Migrate bcrypt PyJWT requests beautifulsoup4 transformers torch playwright psycopg2-binary
fi

# Ensure Playwright browsers are installed (ignore failure if not supported)
python -m playwright install || true
python -m playwright install-deps || true

# Check if using PostgreSQL or SQLite
echo ""
echo "Database Configuration:"
echo "1. PostgreSQL (recommended for production)"
echo "2. SQLite (for quick testing)"
read -p "Choose database [1/2]: " db_choice

if [ "$db_choice" = "1" ]; then
    echo "Starting PostgreSQL with Docker..."
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d postgres
        echo "Waiting for PostgreSQL to start..."
        sleep 5
        export DATABASE_URL="postgresql://admin:admin123@localhost:5432/web_analysis"
    else
        echo "Docker not found. Using SQLite instead."
        export DATABASE_URL="sqlite:///production.db"
    fi
else
    export DATABASE_URL="sqlite:///production.db"
fi

# Initialize database (Flask-Migrate). Falls back to create_all if CLI fails.
export FLASK_APP=app_production.py
echo "Initializing database (migrations)..."
if [ ! -d "migrations" ]; then
  flask db init || true
fi
flask db migrate -m "init" || true
flask db upgrade || true
python -c "from app_production import app, db; app.app_context().push(); db.create_all(); print('Database ensured!')" || true

# Create admin user
echo ""
read -p "Create admin user? [y/n]: " create_admin
if [ "$create_admin" = "y" ]; then
    python -c "
from app_production import app, db, User
app.app_context().push()
username = input('Admin username: ')
email = input('Admin email: ')
password = input('Admin password: ')
user = User(username=username, email=email)
user.set_password(password)
db.session.add(user)
db.session.commit()
print(f'Admin user {username} created!')
"
fi

# Start the application
echo ""
echo "Starting application..."
echo "==========================================="
PORT=${PORT:-5050}
echo "Access the dashboard at: http://localhost:${PORT}"
echo "Features enabled:"
echo "✓ User Authentication"
echo "✓ Real Web Scraping"
echo "✓ Database Persistence"
echo "✓ Sentiment Analysis (mock mode if models not available)"
echo "==========================================="

PORT=${PORT} python app_production.py
