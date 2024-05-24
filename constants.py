VAR_RE = '[^\W0-9]\w*'

FUNCS_TO_INGORE = {
    'set', 'list','round', 'range', 'print', 'sorted', 'max', 'len',
    'range', 'open','read', 'write', 'int', 'str', 'join', 'sum',
    } | {
        f'{VAR_RE}.{func}' for func in {
            'append', 'sort', 'read', 'readlines', 'write', 'split',
            'strip', 'keys', 'items', 'lower', 'upper',
        }
    }

PORT = 1234
MAX_TOKENS = -1
TEMPERATURE = 0.2
STOP_TOKENS=['<|EOT|>', '```']