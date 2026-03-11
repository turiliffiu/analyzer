"""Parser FRU - formato reale log Ericsson"""
import re


class FRUParser:
    def __init__(self, log_content):
        self.lines = log_content.split('\n')

    def parse(self):
        data = []
        in_fru = False

        for line in self.lines:
            # Header reale: "FRU ... ST FAULT OPER MAINT STAT PRODUCTNUMBER ... PMTEMP TEMP UPT VOLT SW"
            if 'FRU' in line and 'PMTEMP' in line and 'TEMP' in line and 'VOLT' in line:
                in_fru = True
                continue

            if in_fru and '===' in line:
                continue

            if in_fru and ('-----' in line or line.strip() == ''):
                if data:
                    break
                continue

            if in_fru and (line.startswith('BB-') or line.startswith('Radio-')):
                parsed = self._parse_row(line)
                if parsed:
                    data.append(parsed)

        return data

    def _parse_row(self, line):
        parts = line.split()
        if len(parts) < 3:
            return None

        name = parts[0]   # BB-1 o Radio-S100-1
        board = parts[2]  # BB6631 o RRU...

        # PMTEMP: cerca pattern "N (OK)" o "N (WARN)"
        pmtemp_match = re.search(r'(\d+\s*\((?:OK|WARN|ALM)\))', line)
        pmtemp = pmtemp_match.group(1) if pmtemp_match else ''

        # TEMP: solo per Radio-*, valore decimale dopo pmtemp
        temp = None
        if name.startswith('Radio-') and pmtemp_match:
            after_pmtemp = line[pmtemp_match.end():]
            temp_match = re.search(r'(\d+(?:\.\d+)?)', after_pmtemp)
            if temp_match:
                try:
                    temp = float(temp_match.group(1))
                except ValueError:
                    pass

        return {
            'name': name,
            'board': board,
            'pmtemp': pmtemp,
            'temp': temp,
            'is_temp_high': temp is not None and temp > 60,
        }
