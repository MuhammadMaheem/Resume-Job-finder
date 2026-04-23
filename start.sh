#!/bin/bash
echo "🤖 Starting Resume Job Matcher AI..."
echo ""

# Check for .env
if [ ! -f backend/.env ]; then
    echo "⚠️  .env not found. Copying from .env.example..."
    cp backend/.env.example backend/.env
    echo "📝 Edit backend/.env and add your GROQ_API_KEY"
fi

# Create venv if needed
if [ ! -d backend/venv ]; then
    echo "🐍 Creating virtual environment..."
    cd backend && python3 -m venv venv && cd ..
    echo "📦 Installing dependencies..."
    cd backend && source venv/bin/activate && pip install -r requirements.txt -q && cd ..
fi

# Kill existing and free ports
echo "🧹 Cleaning up old processes..."
pkill -f "uvicorn backend.main" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
pkill -f "npx vite" 2>/dev/null || true
# Kill processes on specific ports (more aggressive)
for port in 8000 3000 3001; do
    if lsof -ti:$port >/dev/null 2>&1; then
        lsof -ti:$port 2>/dev/null | xargs kill -9 2>/dev/null || true
    fi
done
sleep 3

# Verify ports are free
for port in 8000 3000 3001; do
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "⚠️  Port $port still in use, waiting..."
        sleep 2
    fi
done

# Start backend
echo "📡 Starting backend on http://localhost:8000..."
cd backend && source venv/bin/activate && cd .. && PYTHONPATH=. ./backend/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BGPID=$!

# Wait for backend
for i in $(seq 1 15); do
    sleep 1
    if curl -s --max-time 2 http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "✅ Backend: http://localhost:8000"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "❌ Backend failed"
        exit 1
    fi
done

# Start frontend
echo "🎨 Starting frontend on http://localhost:3000..."
FRONTEND_PORT=3000
FRONTEND_LOG=$(mktemp)
npx vite --host 127.0.0.1 --port $FRONTEND_PORT > "$FRONTEND_LOG" 2>&1 &
FGPID=$!

# Give vite a moment to start, then check for fatal errors
sleep 2
if ! ps -p $FGPID > /dev/null 2>&1; then
    echo "❌ Frontend failed to start:"
    cat "$FRONTEND_LOG"
    rm -f "$FRONTEND_LOG"
    kill $BGPID 2>/dev/null || true
    exit 1
fi

# Check for "port already in use" in logs (might not be fatal if we catch it early)
if grep -qi "Port.*already in use\|EADDRINUSE" "$FRONTEND_LOG" 2>/dev/null; then
    echo "⚠️  Port $FRONTEND_PORT in use, trying $((FRONTEND_PORT + 1))..."
    kill $FGPID 2>/dev/null || true
    wait $FGPID 2>/dev/null || true
    FRONTEND_PORT=$((FRONTEND_PORT + 1))
    sleep 1
    > "$FRONTEND_LOG"
    npx vite --host 127.0.0.1 --port $FRONTEND_PORT > "$FRONTEND_LOG" 2>&1 &
    FGPID=$!
    sleep 2
    if ! ps -p $FGPID > /dev/null 2>&1; then
        echo "❌ Frontend failed on port $FRONTEND_PORT:"
        cat "$FRONTEND_LOG"
        rm -f "$FRONTEND_LOG"
        kill $BGPID 2>/dev/null || true
        exit 1
    fi
fi
rm -f "$FRONTEND_LOG"

# Wait for frontend
for i in $(seq 1 15); do
    sleep 1
    if curl -s --max-time 2 http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
        echo "✅ Frontend: http://localhost:$FRONTEND_PORT"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "❌ Frontend failed"
        kill $BGPID 2>/dev/null || true
        exit 1
    fi
done

echo ""
echo "🎉 Both servers running!"
echo "   👉 Open: http://localhost:$FRONTEND_PORT"
echo "   API:     http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Keep both alive
trap "kill $BGPID $FGPID 2>/dev/null; echo 'Stopped.'; exit" INT TERM
wait
