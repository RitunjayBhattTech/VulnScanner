#!/bin/bash
# VulnAI Scanner - Development Startup Script
# Starts both backend and frontend in development mode

set -e

echo "🚀 Starting VulnAI Scanner in development mode..."
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your API keys before running scans."
fi

# Start backend
echo "📡 Starting backend on port 8000..."
cd backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Start Celery worker
echo "⚙️  Starting Celery worker..."
cd backend
celery -A backend.pipeline.tasks.celery_app worker --loglevel=info -Q scans &
WORKER_PID=$!
cd ..

# Start frontend
echo "🖥️  Starting frontend on port 5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ All services started!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services."

# Trap to kill all background processes
trap "echo 'Shutting down...'; kill $BACKEND_PID $WORKER_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

# Wait for any process to exit
wait