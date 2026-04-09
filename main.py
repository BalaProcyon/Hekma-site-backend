from fastapi import FastAPI
from app.api.router import api_router
from app.core.config import settings
from app.db.database import engine
from app.models import user

# Create tables in the database (better to use Alembic for production migrations)
# user.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
)

app.include_router(api_router, prefix="/api/v1")
