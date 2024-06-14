from python_parsers import get_all_calls, get_all_imports, parse_commented_function, same_ast, remove_docstring, replace_func
from get_code_docs import CodeData, get_reference_docs_custom_functions, get_shortened_docs
from prompts import SYSTEM_PROMPT, DOC_GENERATION_PROMPT
from llm_inference import get_llm_output

import argparse
import pandas as pd
import logging
import ast
import os
import math


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


def get_code_dependancies_and_imports(path):
    import_stmts = []
    code_dependancies = CodeData()
    
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                if os.path.splitext(file)[-1] == '.py':
                    path = os.path.join(root, file)
                    logging.info(f'Extracting dependancies from {path}')
                    
                    with open(path) as f:    
                        code_str = f.read()
                        
                    import_stmts.extend(get_all_imports(code_str)[2])
                    get_all_calls(path, code_str, code_dependancies)
                    
    elif os.path.splitext(path)[-1] == '.py':
        logging.info(f'Extracting dependancies from {path}')
        
        with open(path) as f:    
            code_str = f.read()
        
        import_stmts.extend(get_all_imports(code_str)[2])
        get_all_calls(path, code_str, code_dependancies)
        
    else:
        raise Exception(f'Could not parse path: `{path}`')
    
    import_stmts = list(set(import_stmts))    
        
    return code_dependancies, import_stmts


def generate_documentation_for_custom_calls(code_dependancies, mode, args):
    custom_funcs = [func_name for func_name, func_info in code_dependancies.items() if func_info[CodeData.CUSTOM]]

    num_custom_funcs = len(custom_funcs)
    num_digits = math.ceil(math.log(num_custom_funcs, 10))
    logging.info(f'Generating docs for {len(custom_funcs)} custom functions/methods/classes')

    for i in range(num_custom_funcs):
        least_dep_func = min(custom_funcs, key=lambda x: code_dependancies.undocumented_dependancies(x))
        reason = None
        
        for ri in range(args.max_retries):
            llm_out = get_llm_output(
                SYSTEM_PROMPT, 
                DOC_GENERATION_PROMPT(
                    code_dependancies[least_dep_func][CodeData.CODE], 
                    get_reference_docs_custom_functions(least_dep_func, code_dependancies)
                ),
                mode,
                args,
            )
            
            new_func_code, new_func_node, success, reason = parse_commented_function(least_dep_func, llm_out)
            
            if not success:
                continue
        
            if same_ast(remove_docstring(code_dependancies[least_dep_func][CodeData.NODE]), remove_docstring(new_func_node)):
                code_dependancies.add(
                    least_dep_func,
                    {
                        CodeData.CODE_NEW: '\n'.join([code_dependancies[least_dep_func][CodeData.CODE_INDENT] + line for line in new_func_code.split('\n')]),
                        CodeData.DOC: ast.get_docstring(new_func_node),
                    }
                )
                logging.info(f'\t[{str(i+1).zfill(num_digits)}/{str(num_custom_funcs).zfill(num_digits)}] Generated docs for `{least_dep_func}` in {ri+1}/{args.max_retries} tries')      
                break
            else:
                # with open('debug.func.log', 'a') as f:
                #     print(f'func: {least_dep_func} | try: {ri}', file=f)
                #     print(new_func_code, file=f)
                #     print('-'*10, file=f)
                #     print(code_dependancies[least_dep_func][CodeData.CODE], file=f)
                #     print('-'*42, file=f)
                reason = 'Generated AST does not match original AST'
        else:
            logging.info(f'\t[{str(i+1).zfill(num_digits)}/{str(num_custom_funcs).zfill(num_digits)}] Could not generate docs for `{least_dep_func}` after {args.max_retries} tries')
            logging.info(f'\t\tReason: {reason}')
        
        if code_dependancies[least_dep_func][CodeData.DOC] != '-':
            code_dependancies.add(
                least_dep_func, 
                {CodeData.DOC_SHORT: get_shortened_docs(least_dep_func, CodeData.DOC, args.ref_doc)}
            )            

        custom_funcs.remove(least_dep_func)
        
    custom_funcs_with_docs = [func_name for func_name, func_info in code_dependancies.items() if func_info[CodeData.CUSTOM] and func_info[CodeData.DOC] != '-']
    logging.info(f'Generated docs for {len(custom_funcs_with_docs)}/{num_custom_funcs} custom functions/classes.methods')
    
    
def replace_modified_functions(code_dependancies, path):
    custom_funcs_with_docs = [func_name for func_name, func_info in code_dependancies.items() if func_info[CodeData.CUSTOM] and func_info[CodeData.DOC] != '-']
    
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                if os.path.splitext(file)[-1] == '.py':
                    path = os.path.join(root, file)
                    logging.info(f'Replacing functions in {path}')
                    
                    with open(path) as f:    
                        file_str = f.read()
                        
                    changed = False
                    for func in custom_funcs_with_docs:
                        if code_dependancies[func][CodeData.PATH] == path:
                            changed = True
                            file_str = replace_func(
                                            func, 
                                            code_dependancies[func][CodeData.CODE], 
                                            code_dependancies[func][CodeData.CODE_NEW], 
                                            path,
                                            file_str
                                        )
                            
                    if changed:
                        with open(path, 'w') as f:
                            f.write(file_str)
                    
    elif os.path.splitext(path)[-1] == '.py':
        
        logging.info(f'Replacing functions in {path}')
        
        with open(path) as f:    
            file_str = f.read()
        
        changed = False
        for func in custom_funcs_with_docs:
            if code_dependancies[func][CodeData.PATH] == path:
                changed = True
                file_str = replace_func(
                                func, 
                                code_dependancies[func][CodeData.CODE], 
                                code_dependancies[func][CodeData.CODE_NEW], 
                                path,
                                file_str
                            )
                
        if changed:
            with open(path, 'w') as f:
                f.write(file_str)
        
    else:
        raise Exception(f'Could not parse path: `{path}`')    
