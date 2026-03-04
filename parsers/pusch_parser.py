"""
Parser per dati PUSCH/PUCCH RSSI
Gestisce l'allineamento colonne A, B, C, D usando posizioni header
"""
import re


class PuschParser:
    """Parser per tabella PUSCH/PUCCH con allineamento colonne perfetto"""
    
    def __init__(self, log_content):
        self.lines = log_content.split('\n')
        self.data = []
    
    def parse(self):
        """Parsa la tabella PUSCH/PUCCH"""
        data = []
        in_pusch = False
        header_passed = False
        col_positions = {}
        
        for line in self.lines:
            if 'CELL' in line and 'PUSCH' in line and 'PUCCH' in line:
                in_pusch = True
                col_positions = self._extract_column_positions(line)
                continue
            
            if in_pusch and not header_passed and '====' in line:
                header_passed = True
                continue
            
            if in_pusch and header_passed and (line.strip() == '' or '====' in line):
                break
            
            if in_pusch and header_passed and 'FDD=' in line:
                parsed_row = self._parse_row(line, col_positions)
                if parsed_row:
                    data.append(parsed_row)
        
        return data
    
    def _extract_column_positions(self, header_line):
        """Estrae posizioni colonne A,B,C,D dall'header"""
        positions = {}
        a_match = header_line.find(' A ')
        b_match = header_line.find(' B ')
        c_match = header_line.find(' C ')
        d_match = header_line.find(' D ')
        
        if a_match >= 0: positions['a'] = a_match + 1
        if b_match >= 0: positions['b'] = b_match + 1
        if c_match >= 0: positions['c'] = c_match + 1
        if d_match >= 0: positions['d'] = d_match + 1
        
        return positions
    
    def _parse_row(self, line, col_positions):
        """Parsa riga dati usando posizioni colonne"""
        parts = line.split()
        if len(parts) < 6:
            return None
        
        # Estrai valori porte usando posizioni
        port_a = self._extract_value_at_position(line, col_positions.get('a'))
        port_b = self._extract_value_at_position(line, col_positions.get('b'))
        port_c = self._extract_value_at_position(line, col_positions.get('c'))
        port_d = self._extract_value_at_position(line, col_positions.get('d'))
        
        # Delta: ultimo valore positivo
        delta_match = re.search(r'\s+([\d.]+)\s*$', line)
        delta = float(delta_match.group(1)) if delta_match else None
        
        return {
            'cell': parts[0],
            'sc': parts[1],
            'fru': parts[2],
            'board': parts[3],
            'pusch': float(parts[4]),
            'pucch': float(parts[5]),
            'port_a': port_a,
            'port_b': port_b,
            'port_c': port_c,
            'port_d': port_d,
            'delta': delta,
            'is_rssi_high': any(v and v > -110 for v in [port_a, port_b, port_c, port_d] if v)
        }
    
    def _extract_value_at_position(self, line, col_pos):
        """Estrae valore vicino alla posizione colonna (10 char prima)"""
        if col_pos is None or col_pos >= len(line):
            return None
        
        start = max(0, col_pos - 10)
        end = min(len(line), col_pos + 2)
        window = line[start:end]
        
        match = re.search(r'-[\d.]+', window)
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return None
        return None
