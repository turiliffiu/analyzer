"""Parser FRU - estrazione completa tutti i campi"""
import re


class FRUParser:
    def __init__(self, log_content):
        self.lines = log_content.split('\n')

    def parse(self):
        data = []
        in_fru = False

        for line in self.lines:
            # Header: "FRU ... ST FAULT OPER MAINT STAT PRODUCTNUMBER ... PMTEMP TEMP UPT VOLT SW"
            if 'FRU' in line and 'PMTEMP' in line and 'TEMP' in line and 'VOLT' in line:
                in_fru = True
                continue

            if in_fru and '===' in line:
                continue

            if in_fru and ('-----' in line or line.strip() == ''):
                if data:
                    break
                continue

            if in_fru and (line.startswith('BB-') or line.startswith('Radio-') or line.startswith('AAS-')):
                parsed = self._parse_row(line)
                if parsed:
                    data.append(parsed)

        return data

    def _parse_row(self, line):
        """
        Formato riga FRU:
        FRU          LNH      BOARD              ST FAULT OPER MAINT STAT PRODUCTNUMBER   REV     SERIAL        DATE     PMTEMP  TEMP  UPT VOLT SW
        BB-1         000100   BB6648              1   OFF   ON   OFF   ON KDU1370015/11   R3D     TD3X346968    20211017 4 (OK)       14.1 51
        Radio-S110-1 BXP_5    RRU449944B144B3C    1   OFF   ON   OFF  N/A KRC161787/1     R2D     TU8U0169CY    20211025 4 (OK)  34.4  118 51.8 CXP9013268%15_R101LX
        """
        parts = line.split()
        if len(parts) < 12:
            return None

        # Campi base (posizioni fisse)
        name = parts[0]                # BB-1, Radio-S110-1
        lnh = parts[1]                 # 000100, BXP_5
        board = parts[2]               # BB6648, RRU449944B144B3C
        status = parts[3]              # 1
        fault = parts[4]               # OFF
        oper = parts[5]                # ON
        maint = parts[6]               # OFF
        stat = parts[7]                # ON, N/A
        product_number = parts[8]      # KDU1370015/11
        rev = parts[9]                 # R3D, R2D
        serial = parts[10]             # TD3X346968
        date = parts[11]               # 20211017

        # PMTEMP: cerca pattern "N (OK)" o "N (WARN)" o "N (ALM)"
        pmtemp = ''
        temp = None
        upt = ''
        volt = ''
        sw = ''
        
        pmtemp_match = re.search(r'(\d+\s*\((?:OK|WARN|ALM)\))', line)
        if pmtemp_match:
            pmtemp = pmtemp_match.group(1)
            
            # Estrai la parte dopo PMTEMP
            after_pmtemp = line[pmtemp_match.end():].strip()
            remaining_parts = after_pmtemp.split()
            
            if remaining_parts:
                # Per Radio-* il primo valore è TEMP (decimale)
                if name.startswith('Radio-') or name.startswith('AAS-'):
                    try:
                        temp = float(remaining_parts[0])
                        remaining_parts = remaining_parts[1:]
                    except (ValueError, IndexError):
                        pass
                
                # Prossimi campi: UPT, VOLT, SW (se presente)
                if len(remaining_parts) >= 2:
                    upt = remaining_parts[0]    # 14.1, 118
                    volt = remaining_parts[1]   # 51, 51.8
                    
                    # SW: tutto il resto (solo per Radio)
                    if len(remaining_parts) > 2:
                        sw = ' '.join(remaining_parts[2:])

        # Flag temperatura alta
        is_temp_high = temp is not None and temp > 60

        return {
            'name': name,
            'lnh': lnh,
            'board': board,
            'status': status,
            'fault': fault,
            'oper': oper,
            'maint': maint,
            'stat': stat,
            'product_number': product_number,
            'rev': rev,
            'serial': serial,
            'date': date,
            'pmtemp': pmtemp,
            'temp': temp,
            'upt': upt,
            'volt': volt,
            'sw': sw,
            'is_temp_high': is_temp_high,
        }
