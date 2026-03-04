"""Parser Fiber Links"""
import re

class FiberParser:
    def __init__(self, log_content):
        self.lines = log_content.split('\n')
    
    def parse(self):
        data = []
        in_fiber = False
        for line in self.lines:
            if 'LINK' in line and 'FRU' in line and ('DL' in line or 'UL' in line):
                in_fiber = True
                continue
            if in_fiber and ('----' in line or line.strip() == ''):
                if data:
                    break
                continue
            if in_fiber and 'Radio-' in line:
                parts = line.split()
                if len(parts) >= 2:
                    link, fru = parts[0], parts[1]
                    dl, ul = None, None
                    for p in parts[2:]:
                        try:
                            val = float(p)
                            if dl is None:
                                dl = val
                            elif ul is None:
                                ul = val
                        except:
                            pass
                    data.append({
                        'link': link, 'fru': fru, 'dl_loss': dl, 'ul_loss': ul,
                        'is_dl_critical': dl and abs(dl) > 3.5,
                        'is_ul_critical': ul and abs(ul) > 3.5
                    })
        return data
