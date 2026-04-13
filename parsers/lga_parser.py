"""
Parser per il comando lga (Alarm Log) degli apparati Ericsson.

Formato atteso:
    Timestamp (UTC)     Type Sev    Description
    ======================================================================================================
    2022-03-16 14:23:32 AL   C      License Key File Fault   Lm=1  (Key file fault...)
"""
import re
import logging
from datetime import datetime
from django.utils import timezone as tz
from .base_parser import BaseParser

logger = logging.getLogger(__name__)

# Marker univoco che identifica il blocco LGA
HEADER_MARKER = 'Timestamp (UTC)     Type Sev    Description'

# Regex per ogni riga allarme
# Cattura: timestamp | severità | resto della riga
ALARM_RE = re.compile(
    r'^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+'
    r'AL\s+'
    r'(?P<severity>[CMmw*])\s+'
    r'(?P<rest>.+)$'
)


class LgaParser(BaseParser):
    """
    Parser per il log allarmi LGA degli apparati Ericsson.
    Estrae: timestamp, severity, specific_problem, managed_object, additional_info.
    """

    def parse(self):
        """
        Parsa il blocco LGA e restituisce lista di dizionari.
        Compatibile con il pattern usato dagli altri parser.
        """
        lines = self.lines
        results = []

        # Trova la riga header del blocco LGA
        start_idx = None
        for i, line in enumerate(lines):
            if HEADER_MARKER in line:
                # Saltiamo header + riga di ====
                start_idx = i + 2
                break

        if start_idx is None:
            logger.info("LgaParser: nessun blocco LGA trovato nel log.")
            return results

        for line in lines[start_idx:]:
            stripped = line.strip()

            # Fine blocco: prompt AMOS o riga vuota dopo i dati
            if not stripped:
                continue
            if re.match(r'^[A-Z0-9_-]+>', stripped):
                break

            m = ALARM_RE.match(stripped)
            if not m:
                continue

            timestamp_str = m.group('timestamp')
            severity = m.group('severity')
            rest = m.group('rest')

            # Separa specific_problem / managed_object / additional_info
            specific_problem, managed_object, additional_info = self._split_rest(rest)

            # Parsa timestamp
            try:
                ts = tz.make_aware(datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S"))
            except ValueError:
                logger.warning(f"LgaParser: timestamp non valido: {timestamp_str}")
                continue

            results.append({
                'timestamp': ts,
                'severity': severity,
                'specific_problem': specific_problem,
                'managed_object': managed_object,
                'additional_info': additional_info,
            })

        logger.info(f"LgaParser: parsati {len(results)} allarmi LGA.")
        return results

    def _split_rest(self, rest: str) -> tuple:
        """
        Divide il campo 'rest' in tre componenti:
          - specific_problem : descrizione testuale (senza '=')
          - managed_object   : identificatore MO (contiene '=')
          - additional_info  : testo dentro le parentesi finali

        Esempio input:
          "License Key File Fault              Lm=1  (Key file fault in ME AI: eventId=1)"
        Output:
          ("License Key File Fault", "Lm=1", "Key file fault in ME AI: eventId=1")
        """
        additional_info = ''
        managed_object = ''

        # 1. Estrai additional_info: testo dentro l'ultimo (...)
        paren_match = re.search(r'\((.+)\)\s*$', rest)
        if paren_match:
            additional_info = paren_match.group(1).strip()
            rest = rest[:paren_match.start()].strip()

        # 2. rest ora è: "License Key File Fault              Lm=1"
        #    Splittiamo su 2+ spazi: l'ultimo token è il managed_object
        parts = re.split(r'\s{2,}', rest.strip())

        if len(parts) >= 2:
            specific_problem = parts[0].strip()
            managed_object = parts[-1].strip()
        else:
            # Un solo blocco: potrebbe essere solo il problema o solo il MO
            single = rest.strip()
            if '=' in single:
                specific_problem = ''
                managed_object = single
            else:
                specific_problem = single
                managed_object = ''

        return specific_problem, managed_object, additional_info
