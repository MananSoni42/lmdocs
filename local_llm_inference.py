from constants import PORT, MAX_TOKENS, TEMPERATURE,STOP_TOKENS
import logging
import requests

def clean_output(out):
    for tok in STOP_TOKENS:
        out = out.split(tok)[0].strip()
    return out.strip()

def get_local_llm_output(system_prompt, prompt):
    r = requests.post(
        f'http://localhost:{PORT}/v1/chat/completions', 
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
        logging.error(f'Error while accessing http://localhost:{PORT}/v1/chat/completions: {e}')
        
    return clean_output(output)
