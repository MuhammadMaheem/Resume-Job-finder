"""
Vercel Serverless API Handler for Resume Job Matcher AI.
Uses Mangum to adapt the FastAPI app to Vercel's serverless format.
All /api/* requests are handled by the FastAPI app directly.
"""
import sys
import os

# Add project root to path so we can import from backend/
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

from mangum import Mangum
from backend.main import app

# Export the handler for Vercel
handler = Mangum(app, lifespan="off")
