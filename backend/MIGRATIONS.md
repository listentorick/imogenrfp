# Database Migrations with Alembic

This project uses Alembic for database schema versioning and migrations.

## Setup Complete ✅

- Alembic is configured and initialized
- Database schema is version-controlled
- Migrations run automatically on container startup

## Common Commands

### Creating a New Migration
```bash
# After making changes to models.py
docker-compose exec backend alembic revision --autogenerate -m "Description of changes"
```

### Applying Migrations
```bash
# Apply all pending migrations
docker-compose exec backend alembic upgrade head

# Apply specific migration
docker-compose exec backend alembic upgrade <revision_id>
```

### Rolling Back
```bash
# Rollback one migration
docker-compose exec backend alembic downgrade -1

# Rollback to specific migration
docker-compose exec backend alembic downgrade <revision_id>
```

### Viewing Migration Status
```bash
# Show current migration version
docker-compose exec backend alembic current

# Show migration history
docker-compose exec backend alembic history

# Show pending migrations
docker-compose exec backend alembic show <revision_id>
```

## Workflow for Schema Changes

### Development
1. **Modify models.py** with your changes
2. **Generate migration**: `alembic revision --autogenerate -m "Add new column"`
3. **Review generated migration** in `migrations/versions/`
4. **Test migration**: `alembic upgrade head`
5. **Test rollback**: `alembic downgrade -1` (then upgrade again)

### Production Deployment
1. **Backup database** before deployment
2. **Deploy code** with new migration files
3. **Migrations run automatically** via start-server.sh
4. **Monitor application** after deployment

## Important Notes

- ⚠️ Always backup production database before migrations
- ⚠️ Review auto-generated migrations before applying
- ⚠️ Test rollback procedures in staging first
- ✅ Migrations are automatically applied on container restart
- ✅ Database schema is now fully version-controlled
- ✅ Team can collaborate safely on schema changes

## Migration Files Location
- Configuration: `alembic.ini`
- Environment: `migrations/env.py`
- Migrations: `migrations/versions/`

## Current Status
- Initial migration created from existing schema
- All manual changes (constraints, columns) are now in models.py
- Ready for production-safe schema changes