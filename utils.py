import argparse
import pandas as pd
from get_code_docs import CodeData

def get_args():
    parser = argparse.ArgumentParser()
        
    parser.add_argument(
        "path",
        help="Path to the file/folder of project",
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action='store_true',
        help="Give out verbose logs",
    )

    parser.add_argument(
        "--openai_key",
        help="Your Open AI key",
    )

    parser.add_argument(
        "--openai_key_env",
        help="Environment variable where Open AI key is stored",
    )

    parser.add_argument(
        "--openai_model",
        choices=['gpt-3.5-turbo', 'gpt-4-turbo', 'gpt-4o'],
        default='gpt-3.5-turbo',
        help="Which openAI model to use. Supported models are [gpt-3.5-turbo, gpt-4-turbo, gpt-4o]. gpt-3.5-turbo is used by default",
    )

    parser.add_argument(
        "-p", "--port",
        type=int,
        help="Port where Local LLM server is hosted"
    )

    parser.add_argument(
        "--max_retries",
        type=int,
        default=3,
        help="Number of attempts to give the LLM to generate the documentation for each function"
    )
    
    
    parser.add_argument(
        "--ref_doc",
        choices=['truncate', 'summarize', 'full'],
        default='truncate',
        help="How to process reference documentation. Supported choices are: [truncate / summarize / full] "
    )
        
    args = parser.parse_args()
    verify_args(args)
    
    return args


def verify_args(args):
    parser = argparse.ArgumentParser()

    if not args.port and not args.openai_key and not args.openai_key_env:
        raise parser.error('Use --port for a local LLM or --openai_key/--openai_key_env for openAI LLMs')
    
    if not args.port and (args.openai_model and not (args.openai_key or args.openai_key_env)):
        raise parser.error('One of --openai_key or --openai_key_env must be specified')


def generate_report(code_deps, report_path):
    data = []
    for k,v in code_deps.items():
        if v[CodeData.CUSTOM]:
            data.append({
                'path': v['path'],
                'function': k,
                'documentation': v[CodeData.DOC],
                'shortened documentation': v[CodeData.DOC_SHORT],                
                'code_before': v[CodeData.CODE],
                'code_after': v[CodeData.CODE_NEW]
            })
        
    pd.DataFrame(data).to_csv(report_path, index=False)
