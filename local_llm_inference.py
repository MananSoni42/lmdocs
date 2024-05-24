from constants import PORT, MAX_TOKENS, TEMPERATURE,STOP_TOKENS
import requests

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
    
    status = r.status_code
    output = '-'
    try:
        output = r.json()['choices'][0]['message']['content'].lstrip('\n').strip('\n').strip()
    except:
        print('Error')
        
    return output, status
