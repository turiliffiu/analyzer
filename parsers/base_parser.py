"""
Base Parser per tutti i parser Ericsson
"""
from typing import List, Dict, Any
import re


class BaseParser:
    """
    Classe base per tutti i parser.
    Ogni parser specifico eredita da questa classe.
    """

    def __init__(self, log_content: str):
        self.log_content = log_content
        self.lines = log_content.split('\n')
        self.data = []

    def parse(self) -> List[Dict[str, Any]]:
        """
        Metodo da sovrascrivere nei parser specifici.
        Ritorna lista di dizionari con i dati parsati.
        """
        return []

    def find_section(self, start_marker: str, end_marker: str = None) -> List[str]:
        """
        Trova una sezione del log tra due marker.
        """
        in_section = False
        section_lines = []

        for line in self.lines:
            if start_marker in line:
                in_section = True
                continue
            if end_marker and end_marker in line:
                break
            if in_section:
                section_lines.append(line)

        return section_lines

    def extract_metadata(self) -> Dict[str, str]:
        """
        Estrae metadati generali dal log (apparato, IP, timestamp, SW version).
        """
        metadata = {
            'apparato_nome': '',
            'timestamp': '',
            'ip_address': None,
            'sw_version': ''
        }

        for line in self.lines[:100]:
            # Nome apparato da comando amos
            amos_match = re.search(r'amos\s+([A-Z0-9_-]+)', line, re.IGNORECASE)
            if amos_match and not metadata['apparato_nome']:
                metadata['apparato_nome'] = amos_match.group(1)

            # Timestamp, IP, SW Version tipici nei log Ericsson
            timestamp_match = re.search(
                r'(\d{6}-\d{2}:\d{2}:\d{2}\+\d{4})\s+([\d.]+)\s+([\w.]+)', line
            )
            if timestamp_match:
                metadata['timestamp'] = timestamp_match.group(1)
                metadata['ip_address'] = timestamp_match.group(2)
                metadata['sw_version'] = timestamp_match.group(3)

        return metadata

    @staticmethod
    def is_numeric(value: str) -> bool:
        """Helper per verificare se una stringa è numerica"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def safe_float(value: str, default=None):
        """Converti stringa in float in modo sicuro"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def safe_int(value: str, default=None):
        """Converti stringa in int in modo sicuro"""
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
