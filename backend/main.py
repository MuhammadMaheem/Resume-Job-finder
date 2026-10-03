from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from backend.database import engine, Base, get_db
from backend.routes import router
from backend.config import get_settings
import logging
from contextlib import asynccontextmanager

# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
)
logger = logging.getLogger('jobmatcher')

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

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

# Add rate limiting middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Rate limit exceeded handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    logger.warning(f"Rate limit exceeded: {request.client.host}")
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": "Too many requests. Please wait before making another request.",
            "retry_after": 60
        }
    )

# CORS middleware - restricted in production
# FastAPI CORS middleware doesn't support wildcard subdomains in allow_origins.
# We use allow_origin_regex for wildcard patterns and allow_origins for exact matches.
allowed_origins = []
allowed_origin_regex = None

if settings.CORS_ORIGINS:
    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    regex_parts = []
    
    for origin in origins:
        if origin.startswith("*.") or "*" in origin:
            # Convert wildcard pattern to regex
            # e.g., "https://*.onrender.com" -> "https://[a-z0-9-]+\.onrender\.com"
            pattern = origin.replace(".", r"\.").replace("*", "[a-z0-9-]+")
            regex_parts.append(pattern)
        else:
            allowed_origins.append(origin)
    
    if regex_parts:
        allowed_origin_regex = "^(" + "|".join(regex_parts) + ")$"
else:
    allowed_origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    expose_headers=["Content-Type"],
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
