#!/usr/bin/env bash
set -euo pipefail

# ========= Config =========
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"

# Frontend (Next.js)
FRONTEND_DIR="${FRONTEND_DIR:-$ROOT_DIR/prismchatfrontend2/prismchat}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

# Ports
GATEWAY_PORT="${GATEWAY_PORT:-8080}"
VISION_PORT="${VISION_PORT:-8081}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

# Auto-open browser?
OPEN_BROWSER="${OPEN_BROWSER:-true}"

# If set to "1", skip prompts and auto-install when possible
AUTO_INSTALL="${AUTO_INSTALL:-0}"

# ========= Helpers =========
need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1"
    exit 1
  }
}

confirm() {
  local prompt="$1"
  if [[ "$AUTO_INSTALL" == "1" ]]; then
    return 0
  fi
  read -r -p "$prompt [Y/n] " ans || true
  case "${ans,,}" in
    y|yes|"") return 0 ;;
    *) return 1 ;;
  esac
}

# Consider service "up" if we get any HTTP response code (not 000),
# since some dev servers may return 404/302 on /
wait_http() {
  local url="$1" name="$2" timeout="${3:-120}"
  echo -n "⏳ Waiting for $name at $url "
  local elapsed=0 code="000"
  until code="$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo 000)"; do
    sleep 1
    elapsed=$((elapsed+1))
    if (( elapsed > timeout )); then
      echo
      echo "Timeout waiting for $name ($url)"
      exit 1
    fi
    echo -n "."
  done
  if [[ "$code" == "000" ]]; then
    echo
    echo "❌ Timeout waiting for $name ($url)"
    exit 1
  fi
  echo
  echo "$name ready (HTTP $code)"
}

open_url() {
  local url="$1"
  if [[ "$OPEN_BROWSER" != "true" ]]; then return 0; fi
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$url" >/dev/null 2>&1 || true
  elif command -v open >/dev/null 2>&1; then
    open "$url" >/dev/null 2>&1 || true
  elif command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe start "$url" >/dev/null 2>&1 || true
  fi
}

load_nvm() {
  export NVM_DIR="$HOME/.nvm"
  [[ -s "$NVM_DIR/nvm.sh" ]] && . "$NVM_DIR/nvm.sh"
  [[ -s "$NVM_DIR/bash_completion" ]] && . "$NVM_DIR/bash_completion"
}

install_node_with_nvm() {
  echo "→ Installing Node.js (LTS) via nvm…"
  curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
  load_nvm
  nvm install --lts
  nvm alias default 'lts/*'
  nvm use default
}

ensure_node() {
  load_nvm
  if command -v npm >/dev/null 2>&1 && command -v node >/dev/null 2>&1; then
    return 0
  fi

  echo "ℹ npm/node not found."
  case "$(uname -s)" in
    Linux|Darwin)
      if confirm "Install Node.js (LTS) via nvm now?"; then
        install_node_with_nvm
      else
        echo "npm/node required to run Next.js frontend. Install Node.js and re-run."
        exit 1
      fi
      ;;
    *)
      echo "Unsupported OS for auto-install. Please install Node.js (LTS) manually."
      exit 1
      ;;
  esac

  command -v npm >/dev/null 2>&1 || { echo "npm still not found after install."; exit 1; }
}

port_in_use() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -ltn | grep -q ":${port} "
  elif command -v lsof >/dev/null 2>&1; then
    lsof -iTCP -sTCP:LISTEN -P -n | grep -q ":${port} "
  else
    # Fallback: try connecting with curl
    curl -s -o /dev/null -w "%{http_code}" "http://localhost:${port}/" >/dev/null 2>&1
  fi
}

# ========= Start =========
echo "== PrismGuard dev-up =="

need docker
need curl

# .env info
if [[ ! -f "$ROOT_DIR/.env" ]]; then
  echo "$ROOT_DIR/.env not found. Compose will run but services may miss config."
fi

# Optional: strict env preflight
set -a; [[ -f "$ROOT_DIR/.env" ]] && source "$ROOT_DIR/.env"; set +a
REQUIRED_VARS=(SUPABASE_URL SUPABASE_SERVICE_ROLE_KEY SUPABASE_BUCKET ALLOWED_ORIGINS GOOGLE_API_KEY)
MISS=(); for v in "${REQUIRED_VARS[@]}"; do [[ -z "${!v:-}" ]] && MISS+=("$v"); done
if (( ${#MISS[@]} )); then
  echo "Missing required env vars in .env: ${MISS[*]}"
  exit 1
fi

# 1) Bring up core services
echo "→ docker compose up (Vision, Gateway, Backend)…"
docker compose -f "$COMPOSE_FILE" up -d --build prismguard-vision prismguard-gateway prismchat-backend

# 2) Wait for health endpoints
wait_http "http://localhost:${VISION_PORT}/health"   "Vision"
wait_http "http://localhost:${GATEWAY_PORT}/health"  "Gateway"
wait_http "http://localhost:${BACKEND_PORT}/healthz" "Backend"

# 3) Frontend
FRONTEND_URL=""
if [[ -d "$FRONTEND_DIR" && -f "$FRONTEND_DIR/package.json" ]]; then
  if port_in_use "$FRONTEND_PORT"; then
    echo "ℹ Port ${FRONTEND_PORT} already in use — assuming Next.js is running. Skipping start."
    FRONTEND_URL="http://localhost:${FRONTEND_PORT}"
  else
    echo "→ Starting Next.js dev in $FRONTEND_DIR (PORT=$FRONTEND_PORT)…"
    ensure_node
    pushd "$FRONTEND_DIR" >/dev/null
    if [[ ! -d node_modules ]]; then
      echo "→ Installing frontend deps (npm ci || npm install)…"
      (npm ci || npm install)
    fi
    export NEXT_PUBLIC_BACKEND_URL="http://localhost:${BACKEND_PORT}"
    PORT="${FRONTEND_PORT}" nohup npm run dev >/tmp/prismchat-frontend.log 2>&1 &
    popd >/dev/null
    wait_http "http://localhost:${FRONTEND_PORT}/" "Frontend (Next.js)"
    FRONTEND_URL="http://localhost:${FRONTEND_PORT}"
  fi
else
  # Fallback static demo
  if [[ -f "$ROOT_DIR/frontend/upload-demo.html" ]]; then
    echo "→ Starting static demo on port 5500…"
    if command -v python3 >/dev/null 2>&1; then PYBIN=python3
    elif command -v python  >/dev/null 2>&1; then PYBIN=python
    else
      echo "Python not found for static demo. Install Python or use Next.js."
      exit 1
    fi
    pushd "$ROOT_DIR/frontend" >/dev/null
    nohup "$PYBIN" -m http.server 5500 >/tmp/prismchat-static.log 2>&1 &
    popd >/dev/null
    wait_http "http://localhost:5500/" "Static server"
    FRONTEND_URL="http://localhost:5500/upload-demo.html?gateway=http://localhost:${GATEWAY_PORT}"
  else
    echo "ℹ No frontend found. You can still hit the APIs directly:"
    echo "   Gateway:  http://localhost:${GATEWAY_PORT}"
    echo "   Backend:  http://localhost:${BACKEND_PORT}"
  fi
fi

# 4) Print URLs and optionally open browser
echo
echo "Ready!"
echo "Gateway:   http://localhost:${GATEWAY_PORT}"
echo "Vision:    http://localhost:${VISION_PORT}"
echo "Backend:   http://localhost:${BACKEND_PORT}"
if [[ -n "$FRONTEND_URL" ]]; then
  echo "Frontend:  $FRONTEND_URL"
  open_url "$FRONTEND_URL"
fi
echo
echo "Logs:"
echo "  docker compose logs -f prismguard-vision"
echo "  docker compose logs -f prismguard-gateway"
echo "  docker compose logs -f prismchat-backend"
echo "  tail -f /tmp/prismchat-frontend.log   # Next.js (if used)"
echo "  tail -f /tmp/prismchat-static.log     # Static demo (if used)"
