from constants import MAX_TOKENS, TEMPERATURE,STOP_TOKENS, OPENAI, LOCAL
import logging
import requests
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
    
    
def get_llm_output_local(system_prompt, prompt, port):
    r = requests.post(
        f'http://localhost:{port}/v1/chat/completions', 
        json={
            "messages": [ 
                { "role": "system", "content": system_prompt },
                { "role": "user", "content": prompt }
            ], 
            "temperature": TEMPERATURE, 
            "max_tokens": MAX_TOKENS,
            "stream": False,
            "stop": STOP_TOKENS,
        }
    )
    
    output = '-'
    try:
        output = r.json()['choices'][0]['message']['content'].lstrip('\n').strip('\n').strip()
    except Exception as e:
        raise Exception(f'Error while accessing http://localhost:{port}/v1/chat/completions: {e}')
        
    return clean_output(output)


def get_llm_output_openai(system_prompt, prompt, model, openai_key):
    r = requests.post(
        f'https://api.openai.com/v1/chat/completions', 
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_key}",
        },
        json={
            "model": model,
            "messages": [ 
                { "role": "system", "content": system_prompt },
                { "role": "user", "content": prompt },
            ], 
            "temperature": TEMPERATURE, 
            "max_tokens": MAX_TOKENS,
            "stream": False,
            "stop": STOP_TOKENS,
        }
    )
    
    output = '-'
    try:
        output = r.json()['choices'][0]['message']['content'].lstrip('\n').strip('\n').strip()
    except Exception as e:
        raise Exception(f'Error while accessing https://api.openai.com/v1/chat/completions: {e}')
        
    return clean_output(output)


def get_llm_output(system_prompt, prompt, mode, args):
    if mode == OPENAI:
        return get_llm_output_openai(system_prompt, prompt, args.openai_model, args.openai_key)
    elif mode == LOCAL:
        return get_llm_output_local(system_prompt, prompt, args.port)
    else:
        raise Exception(f'Unknown mode: {mode} for LLM inference')