# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ImogenRFP is a multi-tenant SaaS application for AI-powered RFP (Request for Proposal) processing and response generation. The system uses RAG (Retrieval-Augmented Generation) with ChromaDB and Ollama to automatically extract questions from RFP documents and generate intelligent answers based on a searchable knowledge base.

## Development Commands

### Docker Environment (Recommended)
```bash
# Start all services
docker-compose up -d

# View service logs
docker logs imogenrfp-backend-1
docker logs imogenrfp-worker-1
docker logs imogenrfp-question-worker-1

# Stop all services
docker-compose down
```

### Backend Development
```bash
cd backend
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Database migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head

# Run tests
pytest
```

### Frontend Development
```bash
cd frontend
# Install dependencies
npm install

# Run development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

### Service Access Points
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- ChromaDB: http://localhost:8001
- ChromaDB Browser: http://localhost:3001
- Ollama: http://localhost:11434

## Architecture Overview

### Core Components
- **FastAPI Backend**: REST API with JWT authentication and multi-tenant isolation
- **React Frontend**: SPA with TailwindCSS and React Query for state management
- **PostgreSQL**: Primary database with SQLAlchemy ORM and Alembic migrations
- **ChromaDB**: Vector database for semantic search and RAG functionality
- **Redis**: Task queuing and WebSocket pub/sub for real-time updates
- **Ollama**: Local LLM service (Qwen3:4b model) for AI operations

### Worker Architecture
The system uses specialized background workers:
- **Document Processor Worker**: Extracts text, chunks content, stores in ChromaDB
- **Question Worker**: Performs RAG-based question answering using semantic search
- **Export Worker**: Generates filled-out documents with AI-generated answers

### Data Flow
1. **Project Documents**: Uploaded � processed � stored in ChromaDB for semantic search
2. **Deal Documents**: Uploaded � questions extracted via AI � not stored in ChromaDB
3. **Question Answering**: Questions queued � semantic search ChromaDB � LLM generates answers
4. **Export Generation**: Questions + answers � embedded in original Excel/Word documents

## Multi-Tenant Architecture

All data is strictly isolated by `tenant_id`. Key relationships:
- **Tenant** � Users, Projects, Deals
- **Projects** � Documents (knowledge base, stored in ChromaDB)
- **Deals** � Documents (RFP files, not in ChromaDB) + extracted Questions
- **Questions** � AI-generated Answers

## Queue System

Redis queues handle background processing:
- `document_processing`: File ingestion and text extraction
- `question_processing`: Individual question answering
- `export_jobs`: Document export generation

## Key Services

### Backend Services (`backend/`)
- `queue_service.py`: Redis queue management
- `chroma_service.py`: Vector database operations  
- `question_extraction_service.py`: AI-powered question extraction from documents
- `question_answering_service.py`: RAG-based answer generation
- `export_service.py`: Document export with embedded answers
- `document_processor.py`: File processing worker
- `websocket_manager.py`: Real-time updates to frontend

### Database Models (`backend/models.py`)
Core entities: Tenant, User, Project, Deal, Document, Question, Export
All models include `tenant_id` for multi-tenant isolation.

### API Endpoints (`backend/main.py`)
- Authentication: `/auth/register`, `/auth/login`
- Projects: `/projects/` (knowledge base management)
- Deals: `/deals/` (RFP opportunity management)
- Documents: Upload endpoints for projects vs deals have different behavior
- Questions: `/questions/` (extracted questions and AI answers)
- WebSocket: `/ws` (real-time document processing updates)

## Important Conventions

### File Processing Behavior
- **Project documents**: Stored in ChromaDB for semantic search, used as knowledge base
- **Deal documents**: Questions extracted via AI, original file not stored in ChromaDB
- Excel files use structured cell extraction for better question identification

### Queue Error Handling
Documents can get stuck in "processing" status if workers fail. Check:
1. Redis queue length: `docker exec imogenrfp-redis-1 redis-cli llen document_processing`  
2. Worker logs for processing errors
3. Database document status vs actual queue contents

### Environment Variables
Key environment variables in docker-compose.yml:
- `DATABASE_URL`: PostgreSQL connection
- `REDIS_URL`: Redis connection  
- `CHROMA_HOST/PORT`: ChromaDB connection
- `JWT_SECRET_KEY`: Change in production
- `EXPORT_DIR`: Document export storage

## Common Debugging

### Queue Issues
```bash
# Check queue lengths
docker exec imogenrfp-redis-1 redis-cli llen document_processing
docker exec imogenrfp-redis-1 redis-cli llen question_processing

# View queued jobs
docker exec imogenrfp-redis-1 redis-cli lrange document_processing 0 -1
```

### Database Debugging  
```bash
# Connect to database
docker-compose exec postgres psql -U rfp_user -d rfp_saas

# Check document status
SELECT id, status, original_filename FROM documents WHERE id = 'document-id';
```

### ChromaDB Issues
```bash
# Health check (using API v2)
curl http://localhost:8001/api/v2/heartbeat

# View collections via browser
# http://localhost:3001
```


### Useful endpoints
The backend project has an endpoint that reprocesses project documents

- POST /projects/{project_id}/documents/reprocess
  
This endpoint:

  1. Clears existing chunks from ChromaDB for the project (chroma_service.clear_project_collection())
  2. Finds all processed documents in the project
  3. Resets document status to 'pending'
  4. Re-queues documents for processing using queue_service.enqueue_document_processing()
  5. Returns count of documents being reprocessed
  


## Testing

### Backend Tests
```bash
cd backend
pytest test_question_answering_service.py
pytest test_runner.py
```

### Manual Testing Tools
- ChromaDB Browser at http://localhost:3001 for inspecting vector collections
- FastAPI docs at http://localhost:8000/docs for API testing
- Direct database queries for debugging data issues

## Ollama Integration

The system requires Ollama running with the `qwen3:4b` model for AI operations. The docker-compose setup includes GPU support for NVIDIA cards. Question extraction and answering both use structured JSON output from the LLM.