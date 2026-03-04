# Ericsson Universal Log Analyzer

Applicazione Django per l'analisi automatica dei log degli apparati Ericsson nelle reti di telecomunicazioni.

## Stack

- **Backend:** Django 4.2.9 + Python 3.10+
- **Database:** PostgreSQL
- **Frontend:** Bootstrap 5
- **Export:** openpyxl (Excel multi-sheet)
- **Server:** Gunicorn + Nginx

## Funzionalità

- Upload drag & drop file log (.txt, .log)
- 9 parser modulari: VSWR, PUSCH/PUCCH, Allarmi, FRU, RET/TMA, Fiber Links, SFP, Branch Pairs
- Dashboard con statistiche aggregate
- Visualizzazione analisi dettagliata con 9 tabelle
- Export Excel professionale con 9 fogli formattati
- Storico analisi

## Struttura Progetto

```
analyzer/
├── config/          # Settings, URLs, WSGI
├── core/            # App principale (models, views, forms, templates)
├── exports/         # Excel exporter
├── parsers/         # 9 parser modulari Python
├── scripts/         # Script deploy
├── manage.py
├── requirements.txt
└── .env.example
```

## Setup Sviluppo Locale

```bash
# 1. Clona il repository
git clone <repo-url> analyzer
cd analyzer

# 2. Crea virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Installa dipendenze
pip install -r requirements.txt

# 4. Configura .env
cp .env.example .env
# Modifica .env con i tuoi parametri

# 5. Crea database PostgreSQL
createdb ericsson_db

# 6. Migrazioni e superuser
python manage.py migrate
python manage.py createsuperuser

# 7. Avvia server
python manage.py runserver
```

## Deploy Produzione

```bash
# Su server Ubuntu 22.04
export REPO_URL=https://github.com/<user>/analyzer.git
export DOMAIN=<ip-o-dominio>
sudo bash scripts/deploy.sh
```

Le credenziali vengono salvate in `/root/CREDENTIALS_ANALYZER.txt`.

## Credenziali Default

- Admin: `/admin/` → username `admin`, password generata al deploy
- Credenziali DB: generate automaticamente e salvate in CREDENTIALS_ANALYZER.txt

## Utilizzo

1. Login su `/admin/` o navigazione diretta se già autenticati
2. Upload file log da homepage `/`
3. Attesa parsing automatico (pochi secondi)
4. Visualizzazione analisi dettagliata con 9 tabelle
5. Export Excel dal pulsante nella pagina analisi
