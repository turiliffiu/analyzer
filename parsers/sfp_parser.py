"""Parser SFP Modules"""
import re

class SFPParser:
    def __init__(self, log_content):
        self.lines = log_content.split('\n')
    
    def parse(self):
        data = []
        in_sfp = False
        for line in self.lines:
            if 'PORT' in line and 'FRU' in line and 'TX' in line:
                in_sfp = True
                continue
            if in_sfp and ('----' in line or line.strip() == ''):
                if data:
                    break
                continue
            if in_sfp and line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    port, fru = parts[0], parts[1]
                    is_tn = 'TN' in port or 'IB' in port
                    tx, rx = None, None
                    for p in parts[2:]:
                        if p.startswith('-'):
                            try:
                                val = float(p)
                                if rx is None:
                                    rx = val
                                elif tx is None:
                                    tx = val
                            except:
                                pass
                    data.append({
                        'port': port, 'fru': fru, 'tx_dbm': tx, 'rx_dbm': rx,
                        'is_tn_backhaul': is_tn, 'is_rx_critical': rx and rx < -25
                    })
        return data
