"""Parser Allarmi"""
import re

class AlarmParser:
    def __init__(self, log_content):
        self.lines = log_content.split('\n')
    
    def parse(self):
        data = []
        in_alarms = False
        for line in self.lines:
            if 'ALARM' in line.upper() and 'CAUSE' in line.upper():
                in_alarms = True
                continue
            if in_alarms and ('----' in line or '====' in line):
                if data:
                    break
                continue
            if in_alarms and line.strip():
                severity = None
                if 'CRITICAL' in line.upper():
                    severity = 'CRITICAL'
                elif 'MAJOR' in line.upper():
                    severity = 'MAJOR'
                elif 'MINOR' in line.upper():
                    severity = 'MINOR'
                if severity:
                    remaining = re.sub(r'(CRITICAL|MAJOR|MINOR)', '', line, flags=re.IGNORECASE).strip()
                    alarm_match = re.search(r'([A-Z]\d+)', remaining)
                    alarm_number = alarm_match.group(1) if alarm_match else 'N/A'
                    cause = remaining[alarm_match.end():].strip() if alarm_match else remaining
                    data.append({'severity': severity, 'alarm_number': alarm_number, 'cause': cause[:500]})
        return data
