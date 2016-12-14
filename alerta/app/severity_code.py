"""
Possible alert severity codes.

See ITU-T perceived severity model M.3100 and CCITT Rec X.736
http://tools.ietf.org/html/rfc5674
http://www.itu.int/rec/T-REC-M.3100
http://www.itu.int/rec/T-REC-X.736-199201-I

           ITU Perceived Severity      syslog SEVERITY (Name)
           Critical                    1 (Alert)
           Major                       2 (Critical)
           Minor                       3 (Error)
           Warning                     4 (Warning)
           Indeterminate               5 (Notice)
           Cleared                     5 (Notice)
"""
from alerta.app import status_code

# NOTE: The display text in single quotes can be changed depending on preference.
# eg. CRITICAL = 'critical' or CRITICAL = 'CRITICAL'
ZBX_SEVERITY_MAP = {
    'critical':'disaster',
    'major': 'high',
    'minor': 'average',
    'warning': 'warning',
    'informational': 'information',
    'indeterminate': 'notClassified',
}


def translate_severity(severity):
    return ZBX_SEVERITY_MAP.get(severity, severity)


CRITICAL = translate_severity('critical')
MAJOR = translate_severity('major')
MINOR = translate_severity('minor')
WARNING = translate_severity('warning')
INDETERMINATE = translate_severity('indeterminate')
CLEARED = translate_severity('cleared')
NORMAL = translate_severity('normal')
OK = translate_severity('ok')
INFORM = translate_severity('informational')
DEBUG = translate_severity('debug')
AUTH = translate_severity('security')
UNKNOWN = translate_severity('unknown')
NOT_VALID = translate_severity('notValid')

MORE_SEVERE = 'moreSevere'
LESS_SEVERE = 'lessSevere'
NO_CHANGE = 'noChange'

SEVERITY_MAP = {
    CRITICAL: 1,
    MAJOR: 2,
    MINOR: 3,
    WARNING: 4,
    INFORM: 5,
    INDETERMINATE: 6,
    CLEARED: 7,
    NORMAL: 7,
    OK: 7,
    DEBUG: 8,
    AUTH: 9,
    UNKNOWN: 10  # default
}

_ABBREV_SEVERITY_MAP = {
    CRITICAL: 'Crit',
    MAJOR: 'Majr',
    MINOR: 'Minr',
    WARNING: 'Warn',
    INDETERMINATE: 'Ind ',
    CLEARED: 'Clrd',
    NORMAL: 'Norm',
    OK: 'Ok',
    INFORM: 'Info',
    DEBUG: 'Dbug',
    AUTH: 'Sec ',
    UNKNOWN: 'Unkn',
}

_COLOR_MAP = {
    CRITICAL: '\033[91m',
    MAJOR: '\033[95m',
    MINOR: '\033[93m',
    WARNING: '\033[96m',
    INDETERMINATE: '\033[92m',
    CLEARED: '\033[92m',
    NORMAL: '\033[92m',
    OK: '\033[92m',
    INFORM: '\033[92m',
    DEBUG: '\033[90m',
    AUTH: '\033[90m',
    UNKNOWN: '\033[90m',
}

ENDC = '\033[0m'


def is_valid(name):
    return name in SEVERITY_MAP


def name_to_code(name):
    return SEVERITY_MAP.get(name, SEVERITY_MAP.get(UNKNOWN))


def parse_severity(name):
    if name:
        for severity in SEVERITY_MAP:
            if name.lower() == severity.lower():
                return severity
    return NOT_VALID


def trend(previous, current):
    if name_to_code(previous) > name_to_code(current):
        return MORE_SEVERE
    elif name_to_code(previous) < name_to_code(current):
        return LESS_SEVERE
    else:
        return NO_CHANGE


def status_from_severity(previous_severity, current_severity, current_status=status_code.UNKNOWN):
    if current_severity in [NORMAL, CLEARED, OK]:
        return status_code.CLOSED
    if current_status in [status_code.CLOSED, status_code.EXPIRED]:
        return status_code.OPEN
    if trend(previous_severity, current_severity) == MORE_SEVERE:
        return status_code.OPEN
    return current_status
