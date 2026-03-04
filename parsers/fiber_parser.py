"""Parser Fiber Links - formato reale log Ericsson"""
import re


class FiberParser:
    def __init__(self, log_content):
        self.lines = log_content.split('\n')

    def parse(self):
        data = []
        in_fiber = False

        for line in self.lines:
            # Header reale: "ID LINK RiL    WL1 ... DlLoss UlLoss LENGTH TT"
            if 'DlLoss' in line and 'UlLoss' in line:
                in_fiber = True
                continue

            if in_fiber and '===' in line:
                continue

            if in_fiber and ('-----' in line or line.strip() == ''):
                if data:
                    break
                continue

            if in_fiber and line.strip():
                parsed = self._parse_row(line)
                if parsed:
                    data.append(parsed)

        return data

    def _parse_row(self, line):
        # Formato: " 1 Up   S220-1 1310.00 44C 45% -2.79 -2.48  ... 0.44  0.3  11m 0"
        parts = line.split()
        if len(parts) < 2:
            return None

        # ID numerico in prima posizione
        if not parts[0].isdigit():
            return None

        # link_id e fru (RiL)
        link_id = parts[0]
        fru = parts[2] if len(parts) > 2 else '-'  # es: S220-1

        # DlLoss e UlLoss: ultimi valori numerici prima di LENGTH (Xm)
        # Troviamo la posizione di LENGTH (es: 11m)
        length_idx = None
        for i, p in enumerate(parts):
            if re.match(r'\d+m$', p):
                length_idx = i
                break

        dl_loss, ul_loss = None, None
        if length_idx and length_idx >= 2:
            try:
                ul_loss = float(parts[length_idx - 1])
                dl_loss = float(parts[length_idx - 2])
            except (ValueError, IndexError):
                pass

        return {
            'link': f'Link-{link_id}',
            'fru': f'Radio-{fru}',
            'dl_loss': dl_loss,
            'ul_loss': ul_loss,
            'is_dl_critical': dl_loss is not None and abs(dl_loss) > 3.5,
            'is_ul_critical': ul_loss is not None and abs(ul_loss) > 3.5,
        }
