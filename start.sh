echo "Starting MarketPulse..."
pkill -f "uvicorn.*8001" 2>/dev/null
pkill -f "vite.*5173" 2>/dev/null
cd /Users/dhruvgupta/Projects/MarketPulse
nohup python -m uvicorn backend.app.main:app --port 8001 > /tmp/backend.log 2>&1 &
disown
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID) at http://localhost:8001"
sleep 2
curl -s http://localhost:8001/health > /dev/null && echo "Backend healthy" || echo "Backend failed to start"
cd /Users/dhruvgupta/Projects/MarketPulse/frontend
npm run dev -- --port 5173