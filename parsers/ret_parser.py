"""Parser RET/TMA"""
import re

class RETParser:
    def __init__(self, log_content):
        self.lines = log_content.split('\n')
    
    def parse(self):
        ret_data, tma_data = [], []
        in_ret, header_passed = False, False
        for line in self.lines:
            if 'AntennaUnitGroup' in line and 'AntennaNearUnit' in line:
                in_ret = True
                continue
            if in_ret and not header_passed and '=====' in line:
                header_passed = True
                continue
            if in_ret and header_passed and ('-----' in line or '=====' in line):
                break
            if in_ret and header_passed and 'AntennaUnitGroup=' in line:
                ag_match = re.search(r'AntennaUnitGroup=(\d+)', line)
                anu_match = re.search(r'AntennaNearUnit=(\d+)', line)
                if ag_match and anu_match:
                    parts = line.split()
                    device_data = {
                        'antenna_group': ag_match.group(1),
                        'antenna_near_unit': anu_match.group(1),
                        'status': parts[2] if len(parts) > 2 else '',
                        'device_type': parts[3] if len(parts) > 3 else '',
                        'radio_unit': '', 'product_nr': '', 'revision': '', 'unique_id': ''
                    }
                    if 'TMA' in device_data['device_type'] or 'tma' in device_data['device_type'].lower():
                        tma_data.append(device_data)
                    else:
                        ret_data.append(device_data)
        return {'ret': ret_data, 'tma': tma_data}
