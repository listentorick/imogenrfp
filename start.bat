@echo off
echo 🚀 Starting RFP SaaS Application...

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ✅ .env file created. You may want to customize it before continuing.
)

REM Pull images first to avoid timeout issues
echo 📦 Pulling Docker images...
docker-compose pull

REM Start services
echo 🐳 Starting Docker containers...
docker-compose up -d

REM Wait for services to start
echo ⏳ Waiting for services to start...
timeout /t 15 /nobreak >nul

echo.
echo 🎉 RFP SaaS Application is starting up!
echo.
echo 📱 Frontend: http://localhost:3000
echo 🔧 Backend API: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo 🗄️  ChromaDB: http://localhost:8001
echo.
echo 🔄 To view logs: docker-compose logs -f
echo 🛑 To stop: docker-compose down
echo.
echo 📖 First time setup:
echo   1. Visit http://localhost:3000/register
echo   2. Create your company account
echo   3. Start building your RFP knowledge base!
echo.
pause