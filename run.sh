#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# Synchrony / RelAItion — Full Stack Run Script
# ═══════════════════════════════════════════════════════════════════════

set -e

echo "╔══════════════════════════════════════════════╗"
echo "║  RelAItion — Relationship Intelligence       ║"
echo "╚══════════════════════════════════════════════╝"

# ── Colors
GREEN='\033[0;32m'
AMBER='\033[0;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

# ─── Option 1: Docker (preferred)
if command -v docker &> /dev/null && docker info &> /dev/null 2>&1; then
    echo -e "${GREEN}✓ Docker detected — using Docker Compose${NC}"
    
    # Start everything
    cd "$PROJECT_ROOT"
    docker compose up -d --build
    
    echo ""
    echo -e "${GREEN}✓ PostgreSQL running on port 5433${NC}"
    echo -e "${GREEN}✓ FastAPI backend running on port 8000${NC}"
    
    # Start frontend separately (not in Docker for hot-reload)
    cd "$PROJECT_ROOT/frontend"
    echo -e "${CYAN}→ Starting Next.js frontend...${NC}"
    npm run dev &
    FRONTEND_PID=$!
    
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✓ Backend:  http://localhost:8000${NC}"
    echo -e "${GREEN}  ✓ Frontend: http://localhost:3000${NC}"
    echo -e "${GREEN}  ✓ API Docs: http://localhost:8000/docs${NC}"
    echo -e "${GREEN}  ✓ Database: postgresql://localhost:5433/synchrony${NC}"
    echo -e "${GREEN}════════════════════════════════════════════${NC}"
    echo ""
    echo "Press Ctrl+C to stop all services"
    wait $FRONTEND_PID

# ─── Option 2: Local (no Docker)
else
    echo -e "${AMBER}⚠ Docker not running — using local setup${NC}"
    echo ""
    
    # Check PostgreSQL
    if command -v psql &> /dev/null; then
        echo -e "${GREEN}✓ PostgreSQL CLI found${NC}"
    else
        echo -e "${RED}✗ PostgreSQL not found. Install with: brew install postgresql@16${NC}"
        echo -e "${AMBER}  Then run: brew services start postgresql@16${NC}"
        echo -e "${AMBER}  Then create the database:${NC}"
        echo -e "${AMBER}    createdb synchrony${NC}"
        echo ""
    fi
    
    # Backend
    echo -e "${CYAN}→ Starting backend...${NC}"
    cd "$PROJECT_ROOT/backend"
    
    # Create venv if not exists
    if [ ! -d "venv" ]; then
        echo -e "${CYAN}  Creating Python virtual environment...${NC}"
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install -r requirements.txt -q
    
    # Set fallback DATABASE_URL for local dev
    export DATABASE_URL="${DATABASE_URL:-postgresql://$(whoami)@localhost:5432/synchrony}"
    export JWT_SECRET="${JWT_SECRET:-synchrony-super-secret-jwt-key-2024}"
    
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    sleep 2
    
    # Frontend
    echo -e "${CYAN}→ Starting frontend...${NC}"
    cd "$PROJECT_ROOT/frontend"
    npm run dev &
    FRONTEND_PID=$!
    
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✓ Backend:  http://localhost:8000${NC}"
    echo -e "${GREEN}  ✓ Frontend: http://localhost:3000${NC}"
    echo -e "${GREEN}  ✓ API Docs: http://localhost:8000/docs${NC}"
    echo -e "${GREEN}════════════════════════════════════════════${NC}"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
    wait
fi
