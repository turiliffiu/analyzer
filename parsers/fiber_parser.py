"""Parser Fiber Links - estrazione completa entrambi i lati"""
import re


class FiberParser:
    def __init__(self, log_content):
        self.lines = log_content.split('\n')

    def parse(self):
        data = []
        in_fiber = False

        for line in self.lines:
            # Header: "ID LINK RiL    WL1     TEMP1 TXbs1 TXdBm1 RXdBm1 BER1   WL2 ..."
            if 'DlLoss' in line and 'UlLoss' in line and 'TEMP1' in line:
                in_fiber = True
                continue

            if in_fiber and '===' in line:
                continue

            if in_fiber and ('-----' in line or line.strip() == ''):
                if data:
                    break
                continue

            if in_fiber and line.strip() and line.split()[0].isdigit():
                parsed = self._parse_row(line)
                if parsed:
                    data.append(parsed)

        return data

    def _parse_row(self, line):
        """
        Formato riga Fiber:
        ID LINK RiL    WL1     TEMP1 TXbs1 TXdBm1 RXdBm1 BER1   WL2     TEMP2 TXbs2 TXdBm2 RXdBm2 BER2   DlLoss UlLoss LENGTH TT
         1 Up   S210-1 1310.00 46C   42%   -2.77  -1.94         1310.00 38C   40%   -3.36  -2.68          -0.09  -1.42    52m  0
        """
        parts = line.split()
        if len(parts) < 15:
            return None

        link_id = parts[0]          # 1
        link_status = parts[1]      # Up
        ril = parts[2]              # S210-1

        # Lato 1
        wl1 = self._parse_float(parts[3])           # 1310.00
        temp1 = self._parse_temp(parts[4])          # 46C → 46
        txbs1 = self._parse_percent(parts[5])       # 42% → 42
        txdbm1 = self._parse_float(parts[6])        # -2.77
        rxdbm1 = self._parse_float(parts[7])        # -1.94

        # Trova WL2 (seconda occorrenza di 1310.00 o simile)
        wl2_idx = None
        for i in range(8, len(parts)):
            if re.match(r'\d{4}\.\d{2}', parts[i]):
                wl2_idx = i
                break

        wl2, temp2, txbs2, txdbm2, rxdbm2 = None, None, None, None, None
        dl_loss, ul_loss, length = None, None, ''

        if wl2_idx and wl2_idx + 4 < len(parts):
            # Lato 2
            wl2 = self._parse_float(parts[wl2_idx])
            temp2 = self._parse_temp(parts[wl2_idx + 1])
            txbs2 = self._parse_percent(parts[wl2_idx + 2])
            txdbm2 = self._parse_float(parts[wl2_idx + 3])
            rxdbm2 = self._parse_float(parts[wl2_idx + 4])

            # Loss: dopo RXdBm2, cerca DlLoss UlLoss
            remaining = parts[wl2_idx + 5:]
            if len(remaining) >= 3:
                # Salta eventuale BER2 (vuoto o valore)
                loss_start = 0
                if not self._is_numeric(remaining[0]):
                    loss_start = 1
                
                if len(remaining) > loss_start + 1:
                    dl_loss = self._parse_float(remaining[loss_start])
                    ul_loss = self._parse_float(remaining[loss_start + 1])
                    
                    # LENGTH: cerca pattern "XXm"
                    for part in remaining[loss_start + 2:]:
                        if re.match(r'\d+m$', part):
                            length = part
                            break

        # Flags
        is_dl_critical = dl_loss is not None and abs(dl_loss) > 3.5
        is_ul_critical = ul_loss is not None and abs(ul_loss) > 3.5
        is_link_down = link_status.upper() != 'UP'

        return {
            'link_id': link_id,
            'link_status': link_status,
            'ril': ril,
            'wl1': wl1,
            'temp1': temp1,
            'txbs1': txbs1,
            'txdbm1': txdbm1,
            'rxdbm1': rxdbm1,
            'wl2': wl2,
            'temp2': temp2,
            'txbs2': txbs2,
            'txdbm2': txdbm2,
            'rxdbm2': rxdbm2,
            'dl_loss': dl_loss,
            'ul_loss': ul_loss,
            'length': length,
            'is_dl_critical': is_dl_critical,
            'is_ul_critical': is_ul_critical,
            'is_link_down': is_link_down,
        }

    def _parse_float(self, value):
        """Converte stringa in float, None se fallisce"""
        try:
            return float(value)
        except (ValueError, AttributeError):
            return None

    def _parse_temp(self, value):
        """Estrae temperatura da '46C' → 46"""
        match = re.match(r'(\d+)C?', str(value))
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return None

    def _parse_percent(self, value):
        """Estrae percentuale da '42%' → 42"""
        match = re.match(r'(\d+)%?', str(value))
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return None

    def _is_numeric(self, value):
        """Controlla se è un numero (positivo o negativo)"""
        try:
            float(value)
            return True
        except (ValueError, AttributeError):
            return False
