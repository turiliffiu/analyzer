"""Parser Radio Units VSWR"""
import re

class RadioParser:
    def __init__(self, log_content):
        self.lines = log_content.split('\n')
    
    def parse(self):
        data = []
        in_radio = False
        for line in self.lines:
            if (('FRU' in line and 'VSWR' in line and 'TX' in line) or
                ('FRU' in line and 'BOARD' in line and 'RF' in line and 'BP' in line)):
                in_radio = True
                continue
            if in_radio and '-----' in line:
                break
            if in_radio and 'Radio-' in line:
                parsed = self._parse_radio_line(line)
                if parsed:
                    data.append(parsed)
        return data
    
    def _parse_radio_line(self, line):
        fru_match = re.search(r'(Radio-S\d+-\d+)', line)
        if not fru_match:
            return None
        fru = fru_match.group(1)
        board_match = re.search(r'(RRU[A-Z0-9]+\*?)', line)
        board = board_match.group(1) if board_match else '-'
        rf_match = re.search(r'RRU[A-Z0-9]+\*?\s+([A-D])\s+', line)
        rf_port = rf_match.group(1) if rf_match else '-'
        bp_match = re.search(r'\s+([0-9][A-D])\s+', line)
        branch_pair = bp_match.group(1) if bp_match else '-'
        
        rf_port_index = line.rfind(' ' + rf_port + ' ')
        after_rf = line[rf_port_index + 3:] if rf_port_index >= 0 else line
        
        pairs = []
        for match in re.finditer(r'([\d.]+)\s*\(([\d.]+)\)', after_rf):
            pairs.append({'first': float(match.group(1)), 'second': float(match.group(2)), 'index': match.start()})
        
        standalones = []
        for match in re.finditer(r'([\d.]+)(?!\s*\()', after_rf):
            is_inside = any(match.start() >= p['index'] and match.start() <= p['index'] + 20 for p in pairs)
            if not is_inside:
                try:
                    standalones.append({'value': float(match.group(1)), 'index': match.start()})
                except:
                    pass
        
        tx, tx_unit, vswr, return_loss = None, None, None, None
        
        if len(pairs) == 1:
            vswr = pairs[0]['first']
            return_loss = pairs[0]['second']
            tx_before = [s for s in standalones if s['index'] < pairs[0]['index']]
            if tx_before:
                tx = tx_before[-1]['value']
                tx_unit = 'W' if tx < 100 else 'dBm'
        elif len(pairs) >= 2:
            tx = pairs[0]['first']
            tx_unit = 'dBm' if pairs[0]['second'] > 30 else 'W'
            vswr = pairs[1]['first']
            return_loss = pairs[1]['second']
        
        rx_match = re.search(r'(-[\d.]+)\s+[\d/-]+\s*$', after_rf)
        rx = float(rx_match.group(1)) if rx_match else None
        
        return {
            'fru': fru, 'board': board, 'rf_port': rf_port, 'branch_pair': branch_pair,
            'tx': tx, 'tx_unit': tx_unit, 'vswr': vswr, 'return_loss': return_loss, 'rx': rx,
            'is_vswr_warning': vswr and vswr > 1.25, 'is_vswr_critical': vswr and vswr > 1.50
        }
