FUNCS_TO_INGORE = {
    'set', 'list','round', 'range', 'print', 'sorted', 'max', 'len',
    'range', 'open','read', 'write', 'int', 'str', 'join', 'sum',
    'append', 'sort', 'read', 'readlines', 'write', 'split',
    'strip', 'keys', 'items', 'lower', 'upper', 'get', 'input',
}

PORT = 1234
MAX_TOKENS = 2048
TEMPERATURE = 0.2
STOP_TOKENS=['<|EOT|>', '<STOP>', '###']
MAX_RETRIES = 3