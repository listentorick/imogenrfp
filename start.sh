#!/bin/bash

echo "🚀 Starting RFP SaaS Application..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. You may want to customize it before continuing."
fi

# Pull images first to avoid timeout issues
echo "📦 Pulling Docker images..."
docker-compose pull

# Start services
echo "🐳 Starting Docker containers..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U rfp_user > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
fi

# Check ChromaDB
if curl -s http://localhost:8001/api/v1/heartbeat > /dev/null 2>&1; then
    echo "✅ ChromaDB is ready"
else
    echo "⚠️  ChromaDB may still be starting up..."
fi

# Check Backend API
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ Backend API is ready"
else
    echo "⚠️  Backend API may still be starting up..."
fi

echo ""
echo "🎉 RFP SaaS Application is starting up!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🗄️  ChromaDB: http://localhost:8001"
echo ""
echo "🔄 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down"
echo ""
echo "📖 First time setup:"
echo "  1. Visit http://localhost:3000/register"
echo "  2. Create your company account"
echo "  3. Start building your RFP knowledge base!"