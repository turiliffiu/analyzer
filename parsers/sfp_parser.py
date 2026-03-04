"""Parser SFP Modules - formato reale log Ericsson"""
import re


class SFPParser:
    def __init__(self, log_content):
        self.lines = log_content.split('\n')

    def parse(self):
        data = []
        in_sfp = False

        for line in self.lines:
            # Header reale univoco: contiene "SFPLNH" che non esiste nella tabella Fiber
            if 'SFPLNH' in line and 'TXdBm' in line and 'RXdBm' in line:
                in_sfp = True
                continue

            if in_sfp and '===' in line:
                continue

            if in_sfp and ('-----' in line or line.strip() == ''):
                if data:
                    break
                continue

            if in_sfp and line.strip():
                parsed = self._parse_row(line)
                if parsed:
                    data.append(parsed)

        return data

    def _parse_row(self, line):
        # Formato normale: " 1 S220-1 BB6631  000100  1  ERICSSON  SPP10ELRIDFSEN  10  ...  1310.00 44C  45%  -2.79  -2.48"
        # Formato TN:      "TN        BB6631  000100  IB ERICSSON  EOLS-...         ...  1310    34C  24%  -5.56  -7.93"
        parts = line.split()
        if len(parts) < 8:
            return None

        is_tn = parts[0] == 'TN'

        if not is_tn and not parts[0].isdigit():
            return None

        if is_tn:
            # TN  BOARD  LNH  PORT  VENDOR ...
            fru = parts[1]
            lnh = parts[2]
            port_nr = parts[3]
            vendor_prod = parts[5] if len(parts) > 5 else '-'
        else:
            # ID  RiL  BOARD  LNH  PORT  VENDOR ...
            fru = parts[2]
            lnh = parts[3]
            port_nr = parts[4]
            vendor_prod = parts[6] if len(parts) > 6 else '-'

        port = f'{lnh}/{port_nr}'

        # Temperatura: cerca NNC o NC (es: 44C, 34C)
        temp = None
        temp_match = re.search(r'\b(\d+)C\b', line)
        if temp_match:
            try:
                temp = int(temp_match.group(1))
            except ValueError:
                pass

        # TXdBm e RXdBm: ultimi due valori negativi o float prima di BER
        # Cerchiamo tutti i float con segno opzionale
        float_matches = re.findall(r'(-?\d+\.\d+)', line)
        tx_dbm, rx_dbm = None, None
        # Gli ultimi due float della riga sono TXdBm e RXdBm
        if len(float_matches) >= 2:
            try:
                tx_dbm = float(float_matches[-2])
                rx_dbm = float(float_matches[-1])
            except ValueError:
                pass

        return {
            'port': port,
            'fru': fru,
            'device_name': vendor_prod,
            'tx_dbm': tx_dbm,
            'rx_dbm': rx_dbm,
            'temperature': temp,
            'is_tn_backhaul': is_tn,
            'is_rx_critical': rx_dbm is not None and rx_dbm < -25,
        }
