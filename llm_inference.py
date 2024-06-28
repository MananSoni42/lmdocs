from constants import MAX_TOKENS, TEMPERATURE,STOP_TOKENS, OPENAI, LOCAL, TOK_COUNT
from collections import Counter
import logging
import requests
import os
import json


def clean_output(out):
    """
    Cleans the output string by removing any content following stop tokens.
    
    Input:
    - out (str): The output string to be cleaned.
    
    Returns:
    - str: The cleaned output string with content after stop tokens removed.
    
    Raises:
    - None: This function does not raise any exceptions.
    """
    for tok in STOP_TOKENS:
        # Split the output string at the stop token and take the content before it
        out = out.split(tok)[0].strip()
    return out.strip()


def get_local_llm_name(port):
    """
    Retrieve the local LLM (Large Language Model) name from a given port.

    Input:
    port (int): The port number to query the local server for LLM models.

    Returns:
    str: The name of the first local LLM model if available, otherwise returns '-'.

    Raises:
    Exception: If there is any error while accessing the local server endpoint or processing the response.
    """
    r = requests.get(f'http://localhost:{port}/v1/models')
    output = '-'
    try:
        # Attempt to extract the model name from the response
        output = r.json()['data'][0]['id']
    except Exception as e:
        # Raise an exception if there's an error in the request or response processing
        raise Exception(f'Error while accessing http://localhost:{port}/v1/models: {e}')
    
    return output
    

def get_llm_api_output(url, headers, model, system_prompt, prompt, temperature, max_tokens):
    """
    Sends a POST request to an LLM API and processes the response.

    Input:
        url (str): The URL of the LLM API endpoint.
        headers (dict): HTTP headers to include in the request.
        model (str): The model name to be used for the request.
        system_prompt (str): The system role's content in the message sequence.
        prompt (str): The user's content in the message sequence.
        temperature (float): Sampling temperature for the generation.
        max_tokens (int): Maximum number of tokens to generate.

    Returns:
        tuple: A tuple containing two elements:
            - output (str): The cleaned output text from the API response.
            - usage (Counter): A Counter object representing the token usage.

    Raises:
        Exception: If there is an error accessing the URL or processing the response.
    """
    
    # Initialize usage counter with a copy of TOK_COUNT
    usage = TOK_COUNT.copy()
    
    # Send POST request to the LLM API endpoint
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
        # Extract the output content and usage statistics from the response
        output = r.json()['choices'][0]['message']['content'].lstrip('\n').strip('\n').strip()
        usage = Counter(r.json()['usage'])
    except Exception as e:
        # Raise an exception if there is an error processing the response
        raise Exception(f'Error while accessing {url}: {e}')
        
    return clean_output(output), usage


def get_llm_output(system_prompt, prompt, mode, args):
    """
    Generates the output from a language model based on given prompts and configuration.

    Input:
        system_prompt (str): The system prompt to guide the model's behavior.
        prompt (str): The user prompt for which the model will generate a response.
        mode (str): The mode of model usage, either 'OPENAI' for OpenAI's API or 'LOCAL' for a local model.
        args (Namespace): An object containing necessary arguments, such as API keys, model settings, and other configurations.

    Returns:
        dict: A dictionary containing the API response from the language model.

    Raises:
        Exception: If the 'mode' is neither 'OPENAI' nor 'LOCAL'.
    """
    
    if mode == OPENAI:
        # Use the OpenAI API key from args; fallback to environment variable if not provided
        openai_key = args.openai_key if args.openai_key else os.environ[args.openai_key_env]
        url = 'https://api.openai.com/v1/chat/completions'
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_key}",
        }
        model = args.openai_model
    elif mode == LOCAL:
        # Use a local server for accessing the language model
        url = f'http://localhost:{args.port}/v1/chat/completions'
        headers = {}
        model = 'dummy'
    else:
        # Raise an exception if the mode is not recognized
        raise Exception(f'Unknown mode: `{mode}` for LLM inference')
    
    # Call a helper function to get the actual output from the LLM API
    return get_llm_api_output(url, headers, model, system_prompt, prompt, args.temperature, args.max_tokens)