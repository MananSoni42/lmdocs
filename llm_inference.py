from constants import MAX_TOKENS, TEMPERATURE,STOP_TOKENS, OPENAI, LOCAL, TOK_COUNT
from collections import Counter
import logging
import requests
import os
import json


def clean_output(out):
    for tok in STOP_TOKENS:
        out = out.split(tok)[0].strip()
    return out.strip()


def get_local_llm_name(port):
    r = requests.get(f'http://localhost:{port}/v1/models')
    output = '-'
    try:
        output = r.json()['data'][0]['id']
    except Exception as e:
        raise Exception(f'Error while accessing http://localhost:{port}/v1/models: {e}')
    
    return output
    

def get_llm_api_output(url, headers, model, system_prompt, prompt, temperature, max_tokens):

    usage = TOK_COUNT.copy()
    
    r = requests.post(
        url, 
        headers=headers,
        json={
            "model": model,
            "messages": [ 
                { "role": "system", "content": system_prompt },
                { "role": "user", "content": prompt },
            ], 
            "temperature": temperature, 
            "max_tokens": max_tokens,
            "stream": False,
            "stop": STOP_TOKENS,
        }
    )
    
    output = '-'
    try:
        output = r.json()['choices'][0]['message']['content'].lstrip('\n').strip('\n').strip()
        usage = Counter(r.json()['usage'])
    except Exception as e:
        raise Exception(f'Error while accessing {url}: {e}')
        
    return clean_output(output), usage    


def get_llm_output(system_prompt, prompt, mode, args):
    if mode == OPENAI:
        openai_key = args.openai_key if args.openai_key else os.environ[args.openai_key_env]
        url = 'https://api.openai.com/v1/chat/completions'
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_key}",
        }
        model = args.openai_model
    elif mode == LOCAL:
        url = f'http://localhost:{args.port}/v1/chat/completions'
        headers = {}
        model = 'dummy'
    else:
        raise Exception(f'Unknown mode: `{mode}` for LLM inference')
    
    return get_llm_api_output(url, headers, model, system_prompt, prompt, args.temperature, args.max_tokens)