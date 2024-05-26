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
        "-s", "--summarize_docs",
        action="store_true",
        help="[True/False] Pass an LLM generated summary of known documentation instead of the whole documentation to the LLM"
    )
    
    parser.add_argument(
        "-t", "--truncate_docs",
        action="store_true",
        help="[True/False] Pass only the first paragraph of known documentation instead of the whole documentation to the LLM"
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
                'code_before': v[CodeData.CODE],
                'code_after': v.get('code_updated', '-'),
            })
        
    pd.DataFrame(data).to_csv(report_path, index=False)