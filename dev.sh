#!/usr/bin/env bash
set -euo pipefail

# Kisa monorepo - local development setup
# Usage: ./dev.sh [command]
#   no args   - start all TS services (backend + frontend)
#   postgres  - start only PostgreSQL
#   bot       - start only the Python bot
#   db        - generate Prisma client and push schema
#   build     - build all packages
#   help      - show this help

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}▸${NC} $1"; }
warn() { echo -e "${YELLOW}▸${NC} $1"; }
err() { echo -e "${RED}▸${NC} $1"; }

check_env() {
    if [ ! -f .env ]; then
        err ".env file not found"
        echo "  Copy .env.example to .env and fill in the values:"
        echo "    cp .env.example .env"
        exit 1
    fi
}

check_node() {
    if ! command -v node &>/dev/null; then
        err "Node.js not found. Install Node.js 22+"
        exit 1
    fi
}

check_pnpm() {
    if ! command -v pnpm &>/dev/null; then
        warn "pnpm not found, installing..."
        npm install -g pnpm
    fi
}

cmd_postgres() {
    log "Starting PostgreSQL..."
    docker compose up postgres -d
    log "PostgreSQL running on localhost:5432"
}

cmd_db() {
    check_env
    log "Generating Prisma client..."
    pnpm db:generate
    log "Pushing schema to database..."
    pnpm db:push
    log "Database ready"
}

cmd_dev() {
    check_env
    check_node
    check_pnpm

    log "Starting PostgreSQL..."
    docker compose up postgres -d 2>/dev/null || warn "PostgreSQL may already be running"

    sleep 2

    log "Installing dependencies..."
    pnpm install

    log "Generating Prisma client..."
    pnpm db:generate 2>/dev/null || true

    log "Starting backend + frontend..."
    pnpm dev
}

cmd_bot() {
    check_env

    if ! command -v python3 &>/dev/null; then
        err "Python 3 not found"
        exit 1
    fi

    if [ ! -d "apps/bot/.venv" ]; then
        log "Creating Python venv..."
        python3 -m venv apps/bot/.venv
        source apps/bot/.venv/bin/activate
        pip install -r apps/bot/requirements.txt
    else
        source apps/bot/.venv/bin/activate
    fi

    log "Starting bot..."
    cd apps/bot && python3 main.py
}

cmd_build() {
    log "Building all packages..."
    pnpm turbo build
}

cmd_help() {
    echo "Kisa monorepo - local development"
    echo ""
    echo "Usage: ./dev.sh [command]"
    echo ""
    echo "Commands:"
    echo "  (none)   Start all TS services (backend + frontend)"
    echo "  postgres Start only PostgreSQL"
    echo "  db       Generate Prisma client + push schema"
    echo "  bot      Start the Python bot"
    echo "  build    Build all packages"
    echo "  help     Show this help"
    echo ""
    echo "Examples:"
    echo "  ./dev.sh              # start everything"
    echo "  ./dev.sh postgres     # start DB first"
    echo "  ./dev.sh db           # setup database"
    echo "  ./dev.sh bot          # run the bot"
    echo ""
    echo "First time setup:"
    echo "  cp .env.example .env  # fill in values"
    echo "  ./dev.sh postgres     # start DB"
    echo "  ./dev.sh db           # create tables"
    echo "  ./dev.sh              # start dev servers"
}

case "${1:-}" in
    postgres) cmd_postgres ;;
    db)       cmd_db ;;
    bot)      cmd_bot ;;
    build)    cmd_build ;;
    help|-h|--help) cmd_help ;;
    "")       cmd_dev ;;
    *)
        err "Unknown command: $1"
        echo "  Run ./dev.sh help for usage"
        exit 1
        ;;
esac
