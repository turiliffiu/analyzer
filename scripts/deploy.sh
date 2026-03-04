#!/bin/bash
# =============================================================
#  deploy.sh - Ericsson Universal Log Analyzer
#  Deploy automatico su Ubuntu 22.04 (Proxmox LXC / VM)
#  Uso: sudo bash deploy.sh
# =============================================================

set -e  # Interrompi su errore

# ----------------------------------------------------------
# Colori output
# ----------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'; BOLD='\033[1m'

log()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
step()  { echo -e "\n${BOLD}${BLUE}▶ $1${NC}"; }

# ----------------------------------------------------------
# Configurazione
# ----------------------------------------------------------
APP_NAME="ericsson_analyzer"
APP_DIR="/opt/${APP_NAME}"
VENV_DIR="${APP_DIR}/venv"
REPO_URL="${REPO_URL:-}"   # Imposta con: export REPO_URL=https://github.com/...
USER_APP="www-data"
DOMAIN="${DOMAIN:-$(hostname -I | awk '{print $1}')}"
DJANGO_PORT="8000"

DB_NAME="ericsson_db"
DB_USER="ericsson_user"
DB_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 24)
SECRET_KEY=$(openssl rand -base64 48 | tr -dc 'a-zA-Z0-9!@#$%^&*' | head -c 50)

CREDENTIALS_FILE="/root/CREDENTIALS_ANALYZER.txt"

# ----------------------------------------------------------
# Verifica root
# ----------------------------------------------------------
[[ $EUID -ne 0 ]] && error "Eseguire come root: sudo bash deploy.sh"

step "1. Aggiornamento sistema"
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq \
    python3 python3-pip python3-venv \
    postgresql postgresql-contrib \
    nginx \
    git curl unzip \
    build-essential libpq-dev
log "Pacchetti di sistema installati"

step "2. Configurazione PostgreSQL"
systemctl start postgresql
systemctl enable postgresql

# Crea DB e utente
sudo -u postgres psql << SQLEOF
DO \$\$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DB_USER}') THEN
        CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
    END IF;
END \$\$;

SELECT 'DROP DATABASE IF EXISTS ${DB_NAME}' \gexec
CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
\c ${DB_NAME}
GRANT ALL ON SCHEMA public TO ${DB_USER};
SQLEOF
log "Database PostgreSQL configurato: ${DB_NAME}"

step "3. Clone/aggiornamento applicazione"
if [[ -d "${APP_DIR}/.git" ]]; then
    info "Repository esistente trovato, eseguendo git pull..."
    cd "${APP_DIR}" && git pull origin main
else
    if [[ -z "${REPO_URL}" ]]; then
        # Copia file locali se non c'è repo URL
        warn "REPO_URL non impostato. Copia file da directory corrente..."
        SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
        PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"
        mkdir -p "${APP_DIR}"
        cp -r "${PROJECT_ROOT}/." "${APP_DIR}/"
    else
        git clone "${REPO_URL}" "${APP_DIR}"
    fi
fi
log "Applicazione in ${APP_DIR}"

step "4. Ambiente virtuale Python"
python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r "${APP_DIR}/requirements.txt"
log "Virtual environment configurato"

step "5. File di configurazione .env"
cat > "${APP_DIR}/.env" << ENVEOF
DEBUG=False
SECRET_KEY=${SECRET_KEY}
ALLOWED_HOSTS=${DOMAIN},localhost,127.0.0.1

DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=localhost
DB_PORT=5432
ENVEOF
log ".env creato"

step "6. Setup Django (migrations, staticfiles, superuser)"
cd "${APP_DIR}"
source "${VENV_DIR}/bin/activate"

python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Crea superuser admin
ADMIN_PASSWORD=$(openssl rand -base64 12 | tr -dc 'a-zA-Z0-9' | head -c 12)
python manage.py shell << PYEOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', '${ADMIN_PASSWORD}')
    print("Superuser admin creato")
else:
    print("Superuser admin già esistente")
PYEOF

log "Django configurato"

step "7. Permessi directory"
chown -R "${USER_APP}:${USER_APP}" "${APP_DIR}" 2>/dev/null || true
mkdir -p "${APP_DIR}/media" "${APP_DIR}/logs"
chown -R "${USER_APP}:${USER_APP}" "${APP_DIR}/media" "${APP_DIR}/logs" 2>/dev/null || true
chmod -R 755 "${APP_DIR}"
log "Permessi impostati"

step "8. Configurazione Gunicorn (systemd service)"
cat > /etc/systemd/system/gunicorn_analyzer.service << SVCEOF
[Unit]
Description=Gunicorn - Ericsson Log Analyzer
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=notify
User=${USER_APP}
Group=${USER_APP}
WorkingDirectory=${APP_DIR}
Environment="PATH=${VENV_DIR}/bin"
ExecStart=${VENV_DIR}/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:${DJANGO_PORT} \
    --timeout 120 \
    --access-logfile ${APP_DIR}/logs/gunicorn_access.log \
    --error-logfile ${APP_DIR}/logs/gunicorn_error.log \
    config.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable gunicorn_analyzer
systemctl start gunicorn_analyzer
log "Gunicorn avviato"

step "9. Configurazione Nginx"
cat > /etc/nginx/sites-available/ericsson_analyzer << NGINXEOF
server {
    listen 80;
    server_name ${DOMAIN};

    client_max_body_size 100M;

    access_log /var/log/nginx/analyzer_access.log;
    error_log  /var/log/nginx/analyzer_error.log;

    location /static/ {
        alias ${APP_DIR}/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias ${APP_DIR}/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:${DJANGO_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120;
        proxy_connect_timeout 120;
    }
}
NGINXEOF

ln -sf /etc/nginx/sites-available/ericsson_analyzer /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
log "Nginx configurato e avviato"

step "10. Firewall UFW"
ufw allow 22/tcp   2>/dev/null || true
ufw allow 80/tcp   2>/dev/null || true
ufw allow 443/tcp  2>/dev/null || true
ufw --force enable 2>/dev/null || true
log "Firewall configurato"

# ----------------------------------------------------------
# Salva credenziali
# ----------------------------------------------------------
cat > "${CREDENTIALS_FILE}" << CREDEOF
===================================================
  ERICSSON LOG ANALYZER - CREDENZIALI DEPLOY
  Data: $(date '+%Y-%m-%d %H:%M:%S')
===================================================

URL Applicazione:  http://${DOMAIN}/
URL Admin:         http://${DOMAIN}/admin/

Admin Django:
  Username: admin
  Password: ${ADMIN_PASSWORD}

Database PostgreSQL:
  Database: ${DB_NAME}
  Utente:   ${DB_USER}
  Password: ${DB_PASSWORD}
  Host:     localhost:5432

File applicazione: ${APP_DIR}
Virtual env:       ${VENV_DIR}

Log Gunicorn:
  Access: ${APP_DIR}/logs/gunicorn_access.log
  Error:  ${APP_DIR}/logs/gunicorn_error.log

Comandi utili:
  systemctl status gunicorn_analyzer
  systemctl restart gunicorn_analyzer
  journalctl -u gunicorn_analyzer -f
  nginx -t && systemctl reload nginx
===================================================
CREDEOF

chmod 600 "${CREDENTIALS_FILE}"

# ----------------------------------------------------------
# Riepilogo
# ----------------------------------------------------------
echo ""
echo -e "${BOLD}${GREEN}============================================${NC}"
echo -e "${BOLD}${GREEN}  DEPLOY COMPLETATO CON SUCCESSO!${NC}"
echo -e "${BOLD}${GREEN}============================================${NC}"
echo ""
echo -e "  URL:       ${BOLD}http://${DOMAIN}/${NC}"
echo -e "  Admin:     ${BOLD}http://${DOMAIN}/admin/${NC}"
echo -e "  Credenziali salvate in: ${BOLD}${CREDENTIALS_FILE}${NC}"
echo ""
