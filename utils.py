import argparse
import pandas as pd
from get_function_docs import CodeData

def get_args():
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "path",
        help="Path to the file/folder of project"
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=1234,
        help="Port for Local LLM server"
    )
    
    parser.add_argument(
        "-r", "--ref_doc",
        choices=['truncate', 'summarize', 'full'],
        default='truncate',
        help="[truncate/summarize/full] How to process the reference documents"
    )
    
    parser.add_argument(
        "-key", "--openai_key",
        help="Pass OpenAI key"
    )    
    
    return parser.parse_args()


def verify_args():
    pass #TODO


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
