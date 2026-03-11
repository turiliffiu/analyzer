"""Parser Branch Pairs - formato reale log Ericsson"""
import re


class BranchParser:
    def __init__(self, log_content):
        self.lines = log_content.split('\n')

    def parse(self):
        data = []
        in_branch = False

        for line in self.lines:
            # Header reale: "SC     SE  Tx/Rx BrPair  RfPort1 - RfPort2"
            if 'Tx/Rx' in line and 'BrPair' in line and 'RfPort' in line:
                in_branch = True
                continue

            if in_branch and '===' in line:
                # seconda linea === chiude la sezione
                if data:
                    break
                continue

            if in_branch and line.strip() == '':
                continue

            if in_branch and 'Radio-S' in line:
                parsed = self._parse_row(line)
                if parsed:
                    data.append(parsed)

        return data

    def _parse_row(self, line):
        """
        Formato riga:
        MH45E2 221   2/4 0 (1,2) Radio-S221-1(A) Radio-S221-1(B) RRU2479  TU8U022M1P  FDD=... OK Passed
        """
        # Estrai RfPort1 con lettera porta: Radio-S220-1(A)
        rfport1_match = re.search(r'(Radio-S\d+-\d+)\(([A-D])\)', line)
        if not rfport1_match:
            return None

        fru = rfport1_match.group(1)       # Radio-S220-1
        rf_port = rfport1_match.group(2)   # A

        # Board (HW): codice RRU dopo i due RfPort
        board_match = re.search(r'Radio-S\d+-\d+\([A-D]\)\s+(RRU[A-Z0-9*]+)', line)
        board = board_match.group(1) if board_match else '-'

        # BrPair: primo numero prima di (
        brpair_match = re.search(r'\s(\d+)\s+\(\d+', line)
        branch_pair = brpair_match.group(1) if brpair_match else '-'

        # Risultato: OK, OKW, NOK, NT
        result_match = re.search(r'\s(OK|OKW|NOK|NT)\s', line)
        result = result_match.group(1) if result_match else 'NT'

        return {
            'fru': fru,
            'board': board,
            'rf_port': rf_port,
            'branch_pair': branch_pair,
            'result': result,
            'is_warning': result == 'OKW',
            'is_critical': result == 'NOK',
        }
