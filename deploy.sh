#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file based on .env.production.example"
    exit 1
fi

# Pull latest changes (if using git)
if [ -d .git ]; then
    echo "📥 Pulling latest changes..."
    git pull
fi

# Build and start containers
echo "🔨 Building Docker images..."
docker-compose -f docker-compose.production.yml build

echo "🔄 Stopping old containers..."
docker-compose -f docker-compose.production.yml down

echo "🚀 Starting new containers..."
docker-compose -f docker-compose.production.yml up -d

# Wait for database to be ready
echo "⏳ Waiting for database..."
sleep 10

# Run migrations
echo "📊 Running database migrations..."
docker-compose -f docker-compose.production.yml exec -T web python manage.py migrate --noinput

# Collect static files
echo "📦 Collecting static files..."
docker-compose -f docker-compose.production.yml exec -T web python manage.py collectstatic --noinput

echo "✅ Deployment completed successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Create superuser: docker-compose -f docker-compose.production.yml exec web python manage.py createsuperuser"
echo "2. Check logs: docker-compose -f docker-compose.production.yml logs -f"
echo "3. Access your application at: http://your-server-ip"
