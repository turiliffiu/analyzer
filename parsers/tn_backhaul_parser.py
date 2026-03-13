"""Parser TN Backhaul - Transport Network ports"""
import re


class TNBackhaulParser:
    def __init__(self, log_content):
        self.lines = log_content.split('\n')

    def parse(self):
        """Estrae dati TN backhaul dalle righe che iniziano con 'TN'"""
        data = []
        in_sfp_section = False

        for line in self.lines:
            # Cerca header SFP (dove compaiono le righe TN)
            if 'SFPLNH' in line and 'TXdBm' in line and 'RXdBm' in line:
                in_sfp_section = True
                continue

            if in_sfp_section and '-----' in line:
                # Fine sezione
                if data:
                    break
                continue

            if in_sfp_section and line.strip().startswith('TN'):
                parsed = self._parse_tn_row(line)
                if parsed:
                    data.append(parsed)

        return data

    def _parse_tn_row(self, line):
        """
        Formato TN:
        TN  BOARD  LNH  PORT  VENDOR  VENDORPROD  REV  SERIAL  DATE  ERICSSONPROD  WL  TEMP  TXbs  TXdBm  RXdBm
        TN  BB6648 000100 IB SumitomoElectric SPP5200ER-E5-M A 34T209400124 20230424 NON-ERICSSON 1550 45C 48% -0.17 -19.59
        """
        parts = line.split()
        if len(parts) < 10:
            return None

        if parts[0] != 'TN':
            return None

        # Campi base (sempre presenti)
        board = parts[1]           # BB6648
        lnh = parts[2]             # 000100
        port = parts[3]            # IB, IA2
        vendor = parts[4]          # SumitomoElectric, ERICSSON
        vendor_product = parts[5]  # SPP5200ER-E5-M
        revision = parts[6]        # A, A0
        serial = parts[7]          # 34T209400124
        date = parts[8]            # 20230424

        # ERICSSON PRODUCT: può essere multi-word (es: "RPM777053/1000 R1B")
        # Cerchiamo tutto dopo date fino a WL o NA
        ericsson_product = ''
        i = 9
        while i < len(parts) and not self._is_wavelength_or_na(parts[i]):
            ericsson_product += parts[i] + ' '
            i += 1
        ericsson_product = ericsson_product.strip()

        # Dati ottici (potrebbero essere NA)
        wavelength = None
        temperature = None
        tx_bias = None
        tx_dbm = None
        rx_dbm = None
        has_optical_data = False

        # WL (wavelength)
        if i < len(parts):
            wl = parts[i]
            if wl != 'NA':
                wavelength = wl
                has_optical_data = True
            i += 1

        # TEMP (temperatura)
        if i < len(parts):
            temp_str = parts[i]
            if temp_str != 'NA':
                temp_match = re.match(r'(\d+)C', temp_str)
                if temp_match:
                    temperature = int(temp_match.group(1))
                    has_optical_data = True
            i += 1

        # TXbs (TX bias %)
        if i < len(parts):
            txbs = parts[i]
            if txbs != 'NA':
                tx_bias = txbs
                has_optical_data = True
            i += 1

        # TXdBm
        if i < len(parts):
            try:
                tx_dbm = float(parts[i])
                has_optical_data = True
            except ValueError:
                pass
            i += 1

        # RXdBm
        if i < len(parts):
            try:
                rx_dbm = float(parts[i])
                has_optical_data = True
            except ValueError:
                pass

        # Flag critical RX
        is_rx_critical = rx_dbm is not None and rx_dbm < -25

        return {
            'board': board,
            'lnh': lnh,
            'port': port,
            'vendor': vendor,
            'vendor_product': vendor_product,
            'revision': revision,
            'serial': serial,
            'date': date,
            'ericsson_product': ericsson_product,
            'wavelength': wavelength,
            'temperature': temperature,
            'tx_bias': tx_bias,
            'tx_dbm': tx_dbm,
            'rx_dbm': rx_dbm,
            'is_rx_critical': is_rx_critical,
            'has_optical_data': has_optical_data,
        }

    def _is_wavelength_or_na(self, part):
        """Check if part is wavelength (4 digits) or NA"""
        if part == 'NA':
            return True
        return part.isdigit() and len(part) == 4
