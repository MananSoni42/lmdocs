from collections import Counter

CALLS_TO_INGORE = {
    'set', 'list','round', 'range', 'print', 'sorted', 'max', 'len',
    'range', 'open','read', 'write', 'int', 'str', 'join', 'sum',
    'append', 'sort', 'read', 'readlines', 'write', 'split',
    'strip', 'keys', 'items', 'lower', 'upper', 'get', 'input',
    'isinstance', 'add'
}

MAX_TOKENS = 2048
TEMPERATURE = 0.8
STOP_TOKENS=['<|EOT|>', '<STOP>']
OPENAI = 'openai'
LOCAL = 'local'

TOK_COUNT = Counter({
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
})