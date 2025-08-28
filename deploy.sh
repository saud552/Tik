#!/usr/bin/env bash
set -euo pipefail

# ===== Settings =====
PY_BIN="python3"
PIP_BIN="pip3"
VENV_DIR=".venv"
APP_START="python3 main.py"

# ===== Helpers =====
log() { echo -e "\033[1;34m[INFO]\033[0m $*"; }
warn() { echo -e "\033[1;33m[WARN]\033[0m $*"; }
err() { echo -e "\033[1;31m[ERR ]\033[0m $*"; }

require_cmd() {
	if ! command -v "$1" >/dev/null 2>&1; then
		err "Missing required command: $1"
		exit 1
	fi
}

# ===== 0) Pre-flight =====
log "Starting deployment..."
require_cmd "$PY_BIN"
require_cmd "$PIP_BIN"

# Detect OS family for system dependencies (best-effort)
OS_FAMILY="debian"
if [ -f /etc/os-release ]; then
	. /etc/os-release || true
	case "${ID:-}" in
		ubuntu|debian) OS_FAMILY="debian" ;;
		centos|rhel|rocky|almalinux) OS_FAMILY="rhel" ;;
		*) OS_FAMILY="debian" ;;
	esac
fi

# ===== 1) System dependencies for Playwright/Chromium (best-effort) =====
log "Installing system dependencies (best-effort) for Chromium/Playwright..."
if [ "$OS_FAMILY" = "debian" ]; then
	sudo apt-get update -y || true
	sudo apt-get install -y --no-install-recommends \
		ca-certificates curl xvfb \
		libasound2t64 libasound2-data libatk1.0-0t64 libatk-bridge2.0-0t64 \
		libatspi2.0-0t64 libcairo2 libdbus-1-3 libdrm2 libglib2.0-0t64 \
		libnss3 libnspr4 libx11-6 libxcb1 libxcomposite1 libxdamage1 libxext6 \
		libxfixes3 libxkbcommon0 libxrandr2 libpango-1.0-0 fonts-noto-color-emoji \
		libfontconfig1 libfreetype6 fonts-liberation fonts-freefont-ttf \
		fonts-unifont fonts-ipafont-gothic fonts-wqy-zenhei xfonts-scalable xfonts-cyrillic \
		libgbm1 libgl1-mesa-dri libglx-mesa0 mesa-vulkan-drivers mesa-libgallium || true
elif [ "$OS_FAMILY" = "rhel" ]; then
	sudo yum install -y epel-release || true
	sudo yum install -y \
		alsa-lib atk at-spi2-atk at-spi2-core cairo dbus-libs \
		libdrm glib2 nss nspr libX11 libxcb libXcomposite libXdamage \
		libXext libXfixes libxkbcommon libXrandr pango fontconfig freetype \
		libgbm mesa-dri-drivers xorg-x11-server-Xvfb || true
else
	warn "Unknown OS; skipping system dependencies step"
fi

# ===== 2) Python venv =====
log "Setting up Python virtual environment in $VENV_DIR ..."
if [ ! -d "$VENV_DIR" ]; then
	$PY_BIN -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1090
. "$VENV_DIR/bin/activate"

# Upgrade pip
python -m pip install --upgrade pip

# ===== 3) Python dependencies =====
log "Installing Python requirements..."
pip install -r requirements.txt

# ===== 4) Playwright browsers =====
log "Installing Playwright Chromium browser..."
python -m playwright install --with-deps chromium || true

# ===== 5) App folders =====
log "Creating runtime folders..."
mkdir -p logs data

# ===== 6) Env file =====
if [ ! -f .env ]; then
	warn ".env not found. Creating a minimal template..."
	cat > .env << 'ENV'
TELEGRAM_BOT_TOKEN=
ADMIN_USER_ID=
ENCRYPTION_KEY=
HTTP_TIMEOUT_SECONDS=45
HTTP_MAX_RETRIES=3
HTTP_BACKOFF_FACTOR=0.8
# Optional proxies, example: HTTP_PROXIES="http://user:pass@host:port;https://user:pass@host:port"
HTTP_PROXIES=
ENV
	log "Please edit .env with proper values before running the bot."
fi

# ===== 7) Sanity checks =====
log "Running quick sanity imports..."
python - << 'PY'
import importlib
mods = [
	'core.web_login_automator',
	'core.tiktok_reporter',
	'telegram_bot.bot',
]
for m in mods:
	importlib.import_module(m)
print('Sanity OK')
PY

# ===== 8) How to run =====
log "Deployment completed. To run the bot now, execute:"
echo ""
echo "  source $VENV_DIR/bin/activate"
echo "  $APP_START"
echo ""
log "Notes:"
echo "- Ensure .env has TELEGRAM_BOT_TOKEN and ADMIN_USER_ID."
echo "- First web-login may take time to download browsers if missing."
echo "- For headless issues/CAPTCHA, consider server with proper resources or run non-headless temporarily."