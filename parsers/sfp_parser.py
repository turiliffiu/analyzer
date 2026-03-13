"""Parser SFP Modules - estrazione completa tutti i campi"""
import re


class SFPParser:
    def __init__(self, log_content):
        self.lines = log_content.split('\n')

    def parse(self):
        data = []
        in_sfp = False

        for line in self.lines:
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
        """
        Formato riga SFP - ERICSSON_PRODUCT può essere multi-word!
        ID RiL    BOARD       SFPLNH  PORT VENDOR    VENDORPROD   REV  SERIAL    DATE     ERICSSONPROD   WL   TEMP TXbs TXdBm RXdBm
         1 S210-1 BB6648      000100     1 ERICSSON  EOLP-...     1.0  PM852...  20211020 RDH10265/2 R1A 1310 46C  42%  -2.77 -1.94
        """
        parts = line.split()
        if len(parts) < 15:
            return None

        is_tn = parts[0] == 'TN'

        if is_tn:
            board = parts[1]
            lnh = parts[2]
            port_nr = parts[3]
            vendor = parts[4]
            vendor_prod = parts[5]
            rev = parts[6]
            serial = parts[7]
            date = parts[8]
            # ERICSSON_PRODUCT: da parts[9] fino a prima di WL
            # WL è il primo numero tipo 1310.00 o 1310 o 1550
            wl_idx = self._find_wavelength_index(parts, 9)
            if wl_idx:
                ericsson_product = ' '.join(parts[9:wl_idx])
            else:
                ericsson_product = parts[9]
                wl_idx = 10
            ril = ''
        else:
            if not parts[0].isdigit():
                return None
            ril = parts[1]
            board = parts[2]
            lnh = parts[3]
            port_nr = parts[4]
            vendor = parts[5]
            vendor_prod = parts[6]
            rev = parts[7]
            serial = parts[8]
            date = parts[9]
            # ERICSSON_PRODUCT: da parts[10] fino a prima di WL
            wl_idx = self._find_wavelength_index(parts, 10)
            if wl_idx:
                ericsson_product = ' '.join(parts[10:wl_idx])
            else:
                ericsson_product = parts[10]
                wl_idx = 11

        port = f'{lnh}/{port_nr}'
        
        # Estrai WL, TEMP, TXbs, TX, RX da wl_idx in poi
        remaining = parts[wl_idx:]
        
        wl = None
        temp = None
        txbs = None
        tx_dbm = None
        rx_dbm = None

        if len(remaining) >= 5:
            wl = self._parse_float(remaining[0])
            temp = self._parse_temp(remaining[1])
            txbs = self._parse_percent(remaining[2])
            tx_dbm = self._parse_float(remaining[3])
            rx_dbm = self._parse_float(remaining[4])

        is_rx_critical = rx_dbm is not None and rx_dbm < -25

        return {
            'port': port,
            'fru': board,
            'device_name': vendor_prod,
            'ril': ril,
            'board': board,
            'lnh': lnh,
            'vendor': vendor,
            'rev': rev,
            'serial': serial,
            'date': date,
            'ericsson_product': ericsson_product,
            'wl': wl,
            'temperature': temp,
            'txbs': txbs,
            'tx_dbm': tx_dbm,
            'rx_dbm': rx_dbm,
            'is_tn_backhaul': is_tn,
            'is_rx_critical': is_rx_critical,
        }

    def _find_wavelength_index(self, parts, start_idx):
        """Trova indice di WL (1310, 1310.00, 1550, etc)"""
        for i in range(start_idx, len(parts)):
            # WL è un numero 1000-2000 (nm)
            if re.match(r'^(13\d{2}|15\d{2}|16\d{2})(\.\d+)?$', parts[i]):
                return i
        return None

    def _parse_float(self, value):
        try:
            return float(value)
        except (ValueError, AttributeError):
            return None

    def _parse_temp(self, value):
        match = re.match(r'(\d+)C?', str(value))
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return None

    def _parse_percent(self, value):
        match = re.match(r'(\d+)%?', str(value))
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return None
