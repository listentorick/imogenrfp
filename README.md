# RFP SaaS - Request for Proposal Management System

A comprehensive multi-tenant SaaS application for managing and generating RFP (Request for Proposal) responses using RAG (Retrieval-Augmented Generation) technology.

## Features

- **Multi-tenant Architecture**: Complete tenant isolation with secure data separation
- **Project Management**: Organize RFPs by projects with dedicated standard answers
- **Standard Answers Repository**: Build a searchable knowledge base of reusable answers
- **RAG-Powered Response Generation**: Intelligent answer matching using vector embeddings
- **Templatable Output**: Customizable branded output formats (HTML/Markdown)
- **Containerized Deployment**: Docker-based deployment for scalability

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Primary database with tenant isolation
- **ChromaDB**: Vector database for RAG functionality
- **Redis**: Caching and session management
- **SQLAlchemy**: Database ORM
- **Sentence Transformers**: Text embeddings for semantic search

### Frontend
- **React**: Modern UI framework
- **Tailwind CSS**: Utility-first CSS framework
- **React Query**: Data fetching and state management
- **React Router**: Client-side routing

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-service orchestration

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd imogenrfp
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### First Time Setup

1. **Register a new tenant**
   - Go to http://localhost:3000/register
   - Create your company account
   - This will set up your tenant and admin user

2. **Create your first project**
   - Navigate to Projects section
   - Create a project to organize your RFP responses

3. **Add standard answers**
   - Go to Standard Answers section
   - Add questions and answers to build your knowledge base
   - Use tags to categorize answers

4. **Create an RFP request**
   - Navigate to RFP Requests
   - Create a new RFP with questions
   - Generate AI-powered answers using your knowledge base

## System Architecture

### Multi-Tenant Design
- Database-level tenant isolation
- Secure API endpoints with tenant context
- Isolated vector collections per tenant

### RAG Implementation
- ChromaDB for vector storage
- Sentence Transformers for embeddings
- Semantic similarity search for answer matching
- Configurable similarity thresholds

### Template System
- Jinja2-based templating engine
- Custom branding variables
- HTML and Markdown output formats
- Default templates with customization options

## API Documentation

Once running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

#### Authentication
- `POST /auth/register` - Register new tenant and user
- `POST /auth/login` - User authentication
- `GET /users/me` - Get current user profile

#### Projects
- `GET /projects/` - List tenant projects
- `POST /projects/` - Create new project

#### Standard Answers
- `GET /standard-answers/` - List standard answers
- `POST /standard-answers/` - Create new standard answer
- `POST /standard-answers/bulk-index` - Reindex all answers for RAG

#### RFP Requests
- `GET /rfp-requests/` - List RFP requests
- `POST /rfp-requests/` - Create new RFP request
- `POST /rfp-requests/{id}/generate-answers` - Generate AI answers
- `POST /rfp-requests/{id}/render` - Export formatted response

#### Templates
- `GET /templates/` - List templates
- `POST /templates/` - Create new template

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://rfp_user:rfp_password@postgres:5432/rfp_saas

# Redis
REDIS_URL=redis://redis:6379

# JWT Authentication
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ChromaDB
CHROMA_HOST=chromadb
CHROMA_PORT=8000

# Frontend
REACT_APP_API_URL=http://localhost:8000
```

### Template Variables

Available in all templates:
- `rfp` - RFP request data with questions and answers
- `branding` - Custom branding configuration
- `current_date` - Current date
- `generated_at` - Generation timestamp

Example branding data:
```json
{
  "company_name": "Your Company",
  "logo_url": "https://example.com/logo.png",
  "primary_color": "#007bff",
  "accent_color": "#28a745",
  "contact_email": "contact@company.com",
  "website": "https://company.com"
}
```

## Development

### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
npm install
npm start
```

### Database Migrations

```bash
# In backend directory
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## Production Deployment

### Security Considerations

1. **Change default secrets**
   - Update JWT_SECRET_KEY
   - Change database passwords
   - Use environment-specific configurations

2. **Enable HTTPS**
   - Configure SSL certificates
   - Update CORS settings
   - Secure cookie settings

3. **Database Security**
   - Enable PostgreSQL SSL
   - Configure firewall rules
   - Regular backups

4. **Container Security**
   - Use non-root users
   - Scan images for vulnerabilities
   - Keep dependencies updated

### Scaling

- **Horizontal scaling**: Multiple backend instances behind load balancer
- **Database scaling**: PostgreSQL read replicas
- **Vector database**: ChromaDB cluster for large datasets
- **Caching**: Redis cluster for session management

## Monitoring

### Health Checks
- Database connectivity
- ChromaDB availability
- Redis connectivity

### Metrics
- API response times
- RAG search performance
- Template rendering times
- User activity

## Support

### Common Issues

1. **ChromaDB connection errors**
   - Ensure ChromaDB container is running
   - Check network connectivity
   - Verify port configuration

2. **RAG not finding answers**
   - Run bulk reindex: `POST /standard-answers/bulk-index`
   - Check answer quality and tags
   - Verify embeddings are generated

3. **Template rendering errors**
   - Validate Jinja2 syntax
   - Check variable availability
   - Test with default templates

### Troubleshooting

```bash
# Check container logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs chromadb

# Database connection test
docker-compose exec postgres psql -U rfp_user -d rfp_saas -c "SELECT version();"

# ChromaDB health check
curl http://localhost:8001/api/v1/heartbeat
```

## License

[Your License Here]

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request with description

---

For additional support or questions, please create an issue in the repository.