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

# Kill existing
pkill -f "python main.py" 2>/dev/null
pkill -f "vite" 2>/dev/null
sleep 1

# Start backend
echo "📡 Starting backend on http://localhost:8000..."
cd backend && source venv/bin/activate && python main.py &
BGPID=$!
cd ..

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
npx vite --host 127.0.0.1 --port 3000 &
FGPID=$!

# Wait for frontend
for i in $(seq 1 15); do
    sleep 1
    if curl -s --max-time 2 http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend: http://localhost:3000"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "❌ Frontend failed"
        kill $BGPID 2>/dev/null
        exit 1
    fi
done

echo ""
echo "🎉 Both servers running!"
echo "   👉 Open: http://localhost:3000"
echo "   API:     http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Keep both alive
trap "kill $BGPID $FGPID 2>/dev/null; echo 'Stopped.'; exit" INT TERM
wait
