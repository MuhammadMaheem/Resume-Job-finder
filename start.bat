@echo off
echo Starting Resume Job Matcher AI...
echo.

IF NOT EXIST backend\.env (
    echo .env file not found. Copying from .env.example...
    copy backend\.env.example backend\.env
    echo Please edit backend\.env and add your GROQ_API_KEY
    pause
    exit /b 1
)

echo Starting backend server on port 8000...
start "Backend" /D backend cmd /c "python main.py"

timeout /t 3 /nobreak >nul

echo Starting frontend dev server on port 3000...
start "Frontend" cmd /c "npm run dev"

echo.
echo Both servers starting...
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo.
pause
