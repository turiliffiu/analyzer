"""Parser FRU"""
import re

class FRUParser:
    def __init__(self, log_content):
        self.lines = log_content.split('\n')
    
    def parse(self):
        data = []
        in_fru = False
        for line in self.lines:
            if 'NAME' in line and 'BOARD' in line and 'PMTEMP' in line:
                in_fru = True
                continue
            if in_fru and ('----' in line or line.strip() == ''):
                if data:
                    break
                continue
            if in_fru and (line.startswith('BB-') or line.startswith('Radio-')):
                parts = line.split()
                if len(parts) >= 2:
                    name, board = parts[0], parts[1]
                    pmtemp = parts[2] if len(parts) > 2 else ''
                    temp = None
                    if name.startswith('Radio-') and len(parts) > 3:
                        try:
                            temp = int(parts[3])
                        except:
                            pass
                    data.append({
                        'name': name, 'board': board, 'pmtemp': pmtemp, 'temp': temp,
                        'is_temp_high': temp and temp > 60
                    })
        return data
