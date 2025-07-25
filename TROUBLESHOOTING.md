# Troubleshooting Guide

## Docker Issues

### 1. Docker Desktop Not Running
**Error:** `unable to get image` or `error during connect`

**Solution:**
1. Start Docker Desktop
2. Wait for it to fully initialize (green icon in system tray)
3. Try again: `docker-compose up -d`

### 2. ChromaDB Image Issues
**Error:** `unable to get image 'chromadb/chroma:latest'`

**Solution:**
We've updated to use the correct image: `ghcr.io/chroma-core/chroma:latest`

If still having issues:
```bash
# Pull the image manually
docker pull ghcr.io/chroma-core/chroma:latest

# Or use alternative image
docker pull chromadb/chroma:0.4.18
```

### 3. Port Already in Use
**Error:** `port is already allocated`

**Solutions:**
```bash
# Check what's using the port
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Stop the conflicting process or change ports in docker-compose.yml
```

### 4. Windows/WSL2 Issues

**File System Performance:**
- Ensure your project is in WSL2 file system (`/home/username/`) not Windows (`/mnt/c/`)
- Or enable WSL2 integration in Docker Desktop settings

**Memory Issues:**
- Increase Docker Desktop memory allocation (Settings > Resources > Advanced)
- Recommended: 4GB+ for this application

### 5. Network Issues

**Backend Can't Connect to Database:**
```bash
# Check if containers are on the same network
docker network ls
docker network inspect imogenrfp_default

# Restart with clean network
docker-compose down
docker-compose up -d
```

**CORS Issues:**
- Check that REACT_APP_API_URL in frontend matches your backend URL
- Verify CORS settings in backend/main.py

## Application Issues

### 1. Frontend Won't Load
**Check:**
- Is the frontend container running? `docker-compose ps`
- Check logs: `docker-compose logs frontend`
- Try accessing directly: http://localhost:3000

**Common fixes:**
```bash
# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend
```

### 2. Backend API Errors
**Check:**
- Database connection in logs: `docker-compose logs backend`
- API health: http://localhost:8000/docs

**Common fixes:**
```bash
# Restart backend with fresh DB connection
docker-compose restart backend

# Check database
docker-compose exec postgres psql -U rfp_user -d rfp_saas -c "SELECT version();"
```

### 3. ChromaDB Connection Issues
**Error:** RAG features not working, bulk indexing fails

**Solutions:**
```bash
# Check ChromaDB health
curl http://localhost:8001/api/v1/heartbeat

# Restart ChromaDB
docker-compose restart chromadb

# Clear ChromaDB data (WARNING: deletes all vectors)
docker-compose down
docker volume rm imogenrfp_chromadb_data
docker-compose up -d
```

### 4. Database Issues
**Error:** Database connection refused

**Solutions:**
```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready -U rfp_user

# Reset database (WARNING: deletes all data)
docker-compose down
docker volume rm imogenrfp_postgres_data
docker-compose up -d

# Manual database access
docker-compose exec postgres psql -U rfp_user -d rfp_saas
```

## Development Issues

### 1. Backend Development
```bash
# Run backend locally for development
cd backend
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://rfp_user:rfp_password@localhost:5432/rfp_saas"
export REDIS_URL="redis://localhost:6379"
export CHROMA_HOST="localhost"
export CHROMA_PORT="8001"

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Development
```bash
# Run frontend locally
cd frontend
npm install

# Set environment
export REACT_APP_API_URL="http://localhost:8000"

# Run development server
npm start
```

### 3. Database Migrations
```bash
# Access backend container
docker-compose exec backend bash

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

## Performance Issues

### 1. Slow RAG Responses
**Causes:**
- ChromaDB not indexed
- Large number of standard answers
- Network latency

**Solutions:**
```bash
# Reindex all answers
curl -X POST http://localhost:8000/standard-answers/bulk-index \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check ChromaDB performance
curl http://localhost:8001/api/v1/collections
```

### 2. Slow Container Startup
**Solutions:**
- Increase Docker memory allocation
- Use SSD storage
- Pre-pull images: `docker-compose pull`

## Quick Fixes

### Reset Everything
```bash
# Stop all containers
docker-compose down

# Remove all volumes (WARNING: deletes all data)
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Start fresh
docker-compose up -d
```

### Clean Docker System
```bash
# Remove unused containers, networks, images
docker system prune -a

# Remove unused volumes
docker volume prune
```

### Logs and Debugging
```bash
# View all logs
docker-compose logs

# Follow specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f chromadb

# Access container shell
docker-compose exec backend bash
docker-compose exec postgres bash
```

## Getting Help

1. **Check logs first:** `docker-compose logs`
2. **Verify Docker Desktop is running**
3. **Check port availability**
4. **Try restart:** `docker-compose restart`
5. **Last resort:** Complete reset (see above)

## Windows-Specific Notes

### Using Windows (without WSL2)
- Use `start.bat` instead of `start.sh`
- Use Windows-style paths in volumes if needed
- Ensure Docker Desktop is set to Windows containers

### Using WSL2
- Run commands from WSL2 terminal
- Use `start.sh` script
- Ensure project is in Linux file system for better performance

### PowerShell vs Command Prompt
- PowerShell recommended for better Docker support
- Command Prompt may have issues with some Docker commands