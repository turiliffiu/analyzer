"""
Parser per il comando hget AlarmPort= degli apparati Ericsson.
Usa le posizioni colonna dall'header per gestire valori con spazi singoli.
"""
import re
import logging
from .base_parser import BaseParser

logger = logging.getLogger(__name__)

HEADER_MARKER = 'activeExternalAlarm administrativeState alarmSlogan'
MO_RE = re.compile(
    r'^FieldReplaceableUnit=(?P<fru>[^,]+),AlarmPort=(?P<port>\d+)\s+'
)
ADMIN_STATE_RE = re.compile(r'(\d+)\s+\((\w+)\)')


class AlarmPortParser(BaseParser):
    """Parser porte allarme esterno (hget AlarmPort=)."""

    def parse(self):
        lines = self.lines
        results = []
        start_idx = None
        col_active = col_admin = col_slogan = col_norm = None

        for i, line in enumerate(lines):
            if HEADER_MARKER in line:
                # Leggi posizioni colonne dall'header
                col_active = line.index('activeExternalAlarm')
                col_admin  = line.index('administrativeState')
                col_slogan = line.index('alarmSlogan')
                col_norm   = line.index('normallyOpen')
                start_idx  = i + 2  # salta header + riga ===
                break

        if start_idx is None or col_active is None:
            logger.info("AlarmPortParser: nessun blocco AlarmPort trovato.")
            return results

        for line in lines[start_idx:]:
            stripped = line.strip()
            if stripped.startswith('===') or stripped.startswith('Total:'):
                break
            if not stripped:
                continue

            m = MO_RE.match(stripped)
            if not m:
                continue

            fru  = m.group('fru')
            port = int(m.group('port'))

            # Estrai valori per posizione colonna sulla riga originale
            active_str = line[col_active:col_admin].strip()
            admin_str  = line[col_admin:col_slogan].strip()
            slogan     = line[col_slogan:col_norm].strip()
            norm_str   = line[col_norm:].strip()

            active        = active_str.lower() == 'true'
            normally_open = norm_str.lower() == 'true'

            admin_code = admin_label = ''
            am = ADMIN_STATE_RE.match(admin_str)
            if am:
                admin_code  = am.group(1)
                admin_label = am.group(2)

            results.append({
                'fru':                        fru,
                'alarm_port':                 port,
                'active_external_alarm':      active,
                'administrative_state_code':  admin_code,
                'administrative_state_label': admin_label,
                'alarm_slogan':               slogan,
                'normally_open':              normally_open,
            })

        logger.info(f"AlarmPortParser: parsate {len(results)} porte.")
        return results
