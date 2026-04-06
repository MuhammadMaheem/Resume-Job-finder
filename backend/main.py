from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from database import engine, Base, get_db
from routes import router
from config import get_settings
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
)
logger = logging.getLogger('jobmatcher')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    yield
    # Shutdown
    logger.info("Shutting down")

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered resume analyzer and job matcher",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - restricted in production
allowed_origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )

# Include routes
app.include_router(router, prefix="/api")


@app.get("/api/health")
def health_check():
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        return {"status": "ok", "app": settings.APP_NAME, "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "degraded", "app": settings.APP_NAME, "database": "disconnected"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
