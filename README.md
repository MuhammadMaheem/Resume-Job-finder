# 🤖 Resume Job Matcher AI

An AI-powered resume analyzer and job matching platform that uses Groq's LLM API to analyze your resume, search for matching jobs across the web, and provide personalized job recommendations with direct application links.

## Features

- **📄 Resume Upload & Analysis**: Upload PDF resumes for AI-powered analysis
- **🔍 Intelligent Job Search**: Web search for jobs matching your skills and experience
- **🎯 Smart Job Matching**: AI scores each job based on your resume (0-100%)
- **📊 Resume Scoring**: Get improvement suggestions and identify skill gaps
- **✉️ Cover Letter Generator**: AI-generated personalized cover letters for each job
- **📋 Application Tracker**: Track all your job applications with status management
- **💡 Resume Improvements**: Get keyword suggestions and certification recommendations

## Tech Stack

### Backend
- **FastAPI** - Python web framework
- **Groq API** - LLM inference (Llama 4 Scout)
- **pdfplumber** - PDF text extraction
- **SQLAlchemy** - ORM with SQLite
- **httpx** - Async HTTP client for job searching

### Frontend
- **React + TypeScript** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling with custom blue theme
- **Axios** - HTTP client
- **React Router** - Client-side routing
- **React Dropzone** - File upload

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API key (get from https://console.groq.com)
- SerpAPI key (optional, for better job search - get from https://serpapi.com)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy and configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```
GROQ_API_KEY=your_groq_api_key_here
SERPAPI_KEY=your_serpapi_key_here  # Optional
DATABASE_URL=sqlite:///./resume_chatbot.db
```

5. Start the backend server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend setup

1. Install dependencies (from project root):
```bash
npm install
```

2. Install Vite types:
```bash
npm install -D @types/vite
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Usage

1. **Upload Resume**: Go to the Resume page and upload your PDF resume
2. **Find Jobs**: Go to Find Jobs, select your resume, and click "Scan for Jobs"
3. **View Matches**: Browse AI-scored job listings with match percentages
4. **Apply**: Click "Apply" on any job to go directly to the application page
5. **Track**: Use the Applications page to manage your job search status
6. **Improve**: Get resume improvement suggestions on the Improve Resume page
7. **Cover Letters**: Generate personalized cover letters for any job

## API Endpoints

### Users
- `POST /api/users` - Create user
- `GET /api/users/{id}` - Get user

### Resumes
- `POST /api/resumes/{user_id}/upload` - Upload PDF resume
- `GET /api/resumes/{id}` - Get resume details
- `GET /api/users/{user_id}/resumes` - List user resumes
- `DELETE /api/resumes/{id}` - Delete resume
- `POST /api/resumes/{id}/improvements` - Get improvement suggestions

### Jobs
- `POST /api/jobs/scan` - Scan for matching jobs
- `GET /api/jobs/{id}` - Get job details
- `GET /api/users/{user_id}/jobs` - List user jobs
- `GET /api/users/{user_id}/jobs/top` - Get top matching jobs
- `PATCH /api/jobs/{id}/status` - Update job status

### Cover Letters
- `POST /api/cover-letters/generate` - Generate cover letter
- `GET /api/jobs/{id}/cover-letters` - Get cover letters for job

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React UI      │────▶│   FastAPI       │────▶│   Groq AI       │
│   (Blue Theme)  │◀────│   Backend       │◀────│   (Llama 4)     │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │   SQLite DB     │
                        └─────────────────┘
```

## License

MIT
# Resume-Job-finder
