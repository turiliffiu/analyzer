"""Parser Allarmi - formato reale log Ericsson"""
import re


class AlarmParser:
    def __init__(self, log_content):
        self.lines = log_content.split('\n')

    def parse(self):
        data = []
        in_alarms = False

        for line in self.lines:
            # Header reale: "Date & Time (UTC)   S Specific Problem   MO ..."
            if 'Date & Time' in line and 'Specific Problem' in line:
                in_alarms = True
                continue

            if in_alarms and '===' in line:
                continue

            if in_alarms and line.startswith('>>>'):
                break

            if in_alarms and line.strip() == '':
                continue

            if in_alarms and line.strip():
                parsed = self._parse_row(line)
                if parsed:
                    data.append(parsed)

        return data

    def _parse_row(self, line):
        # Formato: "2026-02-12 08:01:07 C External Alarm   FieldReplaceableUnit=BB-1 (TESTO)"
        # Severity: C=Critical, M=Major, m=Minor, w=Warning(Minor)
        match = re.match(
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+([CMmwW])\s+(.+)',
            line
        )
        if not match:
            return None

        sev_char = match.group(2)
        severity_map = {'C': 'CRITICAL', 'M': 'MAJOR', 'm': 'MINOR', 'w': 'MINOR', 'W': 'MINOR'}
        severity = severity_map.get(sev_char, 'MINOR')

        rest = match.group(3).strip()

        # Separa "Specific Problem" da "MO (AdditionalText)"
        mo_match = re.search(r'\s{2,}(\S.+)', rest)
        if mo_match:
            specific_problem = rest[:mo_match.start()].strip()
            mo_text = mo_match.group(1).strip()
        else:
            specific_problem = rest
            mo_text = ''

        # alarm_number: testo tra parentesi
        add_match = re.search(r'\(([^)]+)\)', mo_text)
        alarm_number = add_match.group(1)[:50] if add_match else specific_problem[:50]

        cause = f'{specific_problem} | {mo_text}' if mo_text else specific_problem

        return {
            'severity': severity,
            'alarm_number': alarm_number,
            'cause': cause[:500],
        }
