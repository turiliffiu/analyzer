"""Parser RET/TMA - formato reale log Ericsson"""
import re


class RETParser:
    def __init__(self, log_content):
        self.lines = log_content.split('\n')

    def parse(self):
        ret_data, tma_data = [], []
        in_ret = False

        for line in self.lines:
            # Header reale: "AntennaNearUnit ... ST TYPE PRODUCTNR REV UNIQUEID RfPort"
            if 'AntennaNearUnit' in line and 'TYPE' in line and 'PRODUCTNR' in line:
                in_ret = True
                continue

            if in_ret and '===' in line:
                continue

            if in_ret and ('-----' in line or line.strip() == ''):
                if ret_data or tma_data:
                    break
                continue

            if in_ret and 'AntennaUnitGroup=' in line:
                parsed = self._parse_row(line)
                if parsed:
                    if 'TMA' in parsed['device_type'].upper():
                        tma_data.append(parsed)
                    else:
                        ret_data.append(parsed)

        return {'ret': ret_data, 'tma': tma_data}

    def _parse_row(self, line):
        # Formato: "AntennaUnitGroup=220,AntennaNearUnit=RET_1500  1  S-RET  86010165  HW_V_A01  KAD241314324A-Y6  FieldReplaceableUnit=Radio-S220-1,RfPort=R"
        ag_match = re.search(r'AntennaUnitGroup=(\S+),AntennaNearUnit=(\S+)', line)
        if not ag_match:
            return None

        antenna_group = ag_match.group(1)
        antenna_near_unit = ag_match.group(2)

        # Campi dopo il match: ST TYPE PRODUCTNR REV UNIQUEID RfPort
        rest = line[ag_match.end():].split()
        if len(rest) < 3:
            return None

        status = rest[0]
        device_type = rest[1]
        product_nr = rest[2] if len(rest) > 2 else ''
        revision = rest[3] if len(rest) > 3 else ''
        unique_id = rest[4] if len(rest) > 4 else ''

        # Radio unit da RfPort field
        ru_match = re.search(r'FieldReplaceableUnit=([\w-]+)', line)
        radio_unit = ru_match.group(1) if ru_match else ''

        return {
            'antenna_group': antenna_group,
            'antenna_near_unit': antenna_near_unit,
            'radio_unit': radio_unit,
            'status': status,
            'device_type': device_type,
            'product_nr': product_nr,
            'revision': revision,
            'unique_id': unique_id,
        }
