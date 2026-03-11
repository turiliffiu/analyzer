# Ericsson Universal Log Analyzer

> Applicazione Django enterprise-grade per l'analisi automatica dei log degli apparati Ericsson nelle reti di telecomunicazioni mobili. Sviluppata per i tecnici **FiberCop TGS** per il troubleshooting degli apparati BTS/RBS Ericsson.

---

## Indice

- [Panoramica](#panoramica)
- [Funzionalità](#funzionalità)
- [Stack Tecnologico](#stack-tecnologico)
- [Architettura](#architettura)
- [Installazione Locale](#installazione-locale)
- [Deploy in Produzione](#deploy-in-produzione)
- [Utilizzo](#utilizzo)
- [Parser Modulari](#parser-modulari)
- [Soglie di Allarme](#soglie-di-allarme)
- [Struttura Progetto](#struttura-progetto)

---

## Panoramica

L'applicazione riceve file di log `.txt` generati dagli script AMOS (Amos Shell) sugli apparati Ericsson, li analizza con 8 parser Python modulari e presenta i risultati in una dashboard web con 9 tabelle interattive e export Excel multi-sheet.

```
Upload Log (.txt) → 8 Parser Python → Database PostgreSQL → Dashboard + Excel
```

---

## Funzionalità

| Funzionalità | Dettaglio |
|---|---|
| Upload drag & drop | File `.txt` e `.log`, max 50 MB |
| Parsing automatico | 8 parser modulari eseguiti in sequenza |
| Dashboard storico | Statistiche aggregate su tutte le analisi |
| Analisi dettagliata | 9 tabelle con evidenziazione valori critici |
| Export Excel | 9 fogli formattati con colori e auto-sizing |
| Autenticazione | Login obbligatorio, gestione utenti Django Admin |
| API REST | Endpoint JSON per integrazioni future (MARS) |

---

## Stack Tecnologico

| Layer | Tecnologia |
|---|---|
| Backend | Django 4.2.9 + Python 3.10+ |
| Database | PostgreSQL 14+ |
| Frontend | Bootstrap 5.3 + JavaScript vanilla |
| Export | openpyxl 3.1 |
| Server | Gunicorn 21 + Nginx |
| Deploy | Script bash automatico (Ubuntu 22.04) |

---

## Architettura

```
Browser
  │
  ▼
Nginx (reverse proxy, static files)
  │
  ▼
Gunicorn (3 workers, WSGI)
  │
  ▼
Django Application
  │
  ├── UploadView ──────► Parser Factory
  │                           │
  │          ┌────────────────┼────────────────┐
  │          ▼                ▼                ▼
  │    RadioParser      AlarmParser      FRUParser
  │    PuschParser      RETParser        FiberParser
  │    SFPParser        BranchParser
  │          │
  │          ▼
  │    Analysis + 11 Models → PostgreSQL
  │
  ├── DashboardView ────► statistiche aggregate
  ├── AnalysisDetailView ► 9 tabelle dati
  └── ExportExcelView ──► file .xlsx download
```

---

## Installazione Locale

```bash
# 1. Clone
git clone https://github.com/turiliffiu/analyzer.git
cd analyzer

# 2. Virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Database PostgreSQL
su - postgres -c "psql -c \"CREATE USER ericsson_user WITH PASSWORD 'dev_password';\""
su - postgres -c "psql -c \"CREATE DATABASE ericsson_db OWNER ericsson_user;\""
su - postgres -c "psql -d ericsson_db -c \"GRANT ALL ON SCHEMA public TO ericsson_user;\""

# 4. Configurazione
cp .env.example .env
# Modifica .env con le tue credenziali

# 5. Setup Django
python manage.py migrate
python manage.py createsuperuser

# 6. Avvio
python manage.py runserver 0.0.0.0:8000
```

---

## Deploy in Produzione

Su un server Ubuntu 22.04 fresco:

```bash
export REPO_URL=https://github.com/turiliffiu/analyzer.git
export DOMAIN=<ip-o-dominio>
git clone $REPO_URL /tmp/analyzer_setup
sudo bash /tmp/analyzer_setup/scripts/deploy.sh
```

Lo script installa e configura automaticamente: PostgreSQL, Gunicorn (systemd service), Nginx, firewall UFW. Le credenziali generate vengono salvate in `/root/CREDENTIALS_ANALYZER.txt`.

**Requisiti server:** Ubuntu 22.04 LTS, 2 CPU, 4 GB RAM, 32 GB disk.

---

## Utilizzo

1. Accedi con le credenziali admin su `http://<server>/admin/`
2. Naviga su `http://<server>/` per la pagina di upload
3. Trascina o seleziona un file log Ericsson (`.txt`)
4. Attendi il parsing automatico (2-10 secondi)
5. Visualizza l'analisi nelle 9 tabelle interattive
6. Clicca **Export Excel** per scaricare il report completo

---

## Parser Modulari

Ogni parser è una classe Python indipendente in `parsers/`. Tutti ricevono il contenuto grezzo del log come stringa e restituiscono una lista di dizionari.

| Parser | File | Dati estratti |
|---|---|---|
| `BaseParser` | `base_parser.py` | Metadati apparato: nome, IP, SW version, timestamp |
| `RadioParser` | `radio_parser.py` | Radio Units VSWR, TX, RX, Return Loss |
| `AlarmParser` | `alarm_parser.py` | Allarmi attivi con severity C/M/m/w |
| `FRUParser` | `fru_parser.py` | Field Replaceable Units con temperature |
| `PuschParser` | `pusch_parser.py` | RSSI PUSCH/PUCCH per porta A/B/C/D |
| `RETParser` | `ret_parser.py` | Dispositivi RET e TMA separati |
| `FiberParser` | `fiber_parser.py` | Perdita fibra DL/UL per ogni link |
| `SFPParser` | `sfp_parser.py` | Moduli SFP con TX/RX dBm e temperatura |
| `BranchParser` | `branch_parser.py` | Test branch pairs OK/OKW/NOK/NT |

---

## Soglie di Allarme

| Parametro | Warning | Critical |
|---|---|---|
| VSWR | > 1.25 | > 1.50 |
| RSSI PUSCH/PUCCH | — | > -110 dBm |
| Temperatura FRU | — | > 60 °C |
| Fiber Loss DL/UL | — | > 3.5 dB (valore assoluto) |
| SFP RX | — | < -25 dBm |
| Branch Pair | OKW | NOK |

---

## Struttura Progetto

```
analyzer/
├── config/                  # Configurazione Django
│   ├── settings.py          # Settings con python-decouple
│   ├── urls.py              # URL root
│   └── wsgi.py
├── core/                    # App principale
│   ├── models.py            # 11 modelli Django
│   ├── views.py             # 4 view (Upload, Dashboard, Detail, Export)
│   ├── forms.py             # Form upload con validazione
│   ├── admin.py             # Django Admin configurato
│   ├── urls.py              # URL app
│   ├── migrations/          # Migration database
│   └── templates/core/      # 4 template Bootstrap
│       ├── base.html
│       ├── upload.html
│       ├── dashboard.html
│       └── analysis_detail.html
├── parsers/                 # 9 parser modulari
│   ├── base_parser.py
│   ├── radio_parser.py
│   ├── alarm_parser.py
│   ├── fru_parser.py
│   ├── pusch_parser.py
│   ├── ret_parser.py
│   ├── fiber_parser.py
│   ├── sfp_parser.py
│   └── branch_parser.py
├── exports/
│   └── excel_exporter.py    # Export Excel 9 fogli
├── scripts/
│   └── deploy.sh            # Deploy automatico Ubuntu 22.04
├── .env.example             # Template variabili ambiente
├── requirements.txt
└── pytest.ini
```

---

## Variabili Ambiente (.env)

```env
DEBUG=False
SECRET_KEY=<chiave-segreta-50-caratteri>
ALLOWED_HOSTS=<ip-o-dominio>,localhost

DB_NAME=ericsson_db
DB_USER=ericsson_user
DB_PASSWORD=<password>
DB_HOST=localhost
DB_PORT=5432
```

---

## Comandi Utili (Produzione)

```bash
# Stato servizi
systemctl status gunicorn_analyzer
systemctl status nginx

# Riavvio dopo aggiornamento
cd /opt/ericsson_analyzer
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart gunicorn_analyzer
nginx -t && systemctl reload nginx

# Log in tempo reale
journalctl -u gunicorn_analyzer -f
tail -f /opt/ericsson_analyzer/logs/gunicorn_error.log
```

---

*Ericsson Universal Log Analyzer — FiberCop TGS © 2025*
