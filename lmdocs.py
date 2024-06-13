from python_parsers import get_all_calls, get_all_imports, parse_commented_function, same_ast, remove_docstring, replace_func
from get_code_docs import CodeData, get_known_function_docs, get_reference_docs, get_shortened_docs
from prompts import SYSTEM_PROMPT, DOC_GENERATION_PROMPT
from constants import LOCAL, OPENAI
from llm_inference import get_llm_output, get_local_llm_name, get_llm_output_local
from utils import get_args, generate_report

import ast
import os
import copy
import logging
import math


import sys
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

def main():
    
    args = get_args()    
        
    path = args.path
    logging.info(f'Project path: {path}')
    
    mode = LOCAL if args.port else OPENAI
    logging.info(f'mode: {mode}')
    model_name = get_local_llm_name(args.port) if mode == LOCAL else args.openai_model
    logging.info(f'Using {mode} LLM: {model_name}')
    

    import_stmts = []
    code_dependancies = CodeData()
    
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                if os.path.splitext(file)[-1] == '.py':
                    path = os.path.join(root, file)
                    logging.info(f'\tExtracting dependancies from {path}')
                    
                    with open(path) as f:    
                        code_str = f.read()
                        
                    import_stmts.extend(get_all_imports(code_str)[2])
                    get_all_calls(path, code_str, code_dependancies)
                    
    elif os.path.splitext(path)[-1] == '.py':
        logging.info(f'\tExtracting dependancies from {path}')
        
        with open(path) as f:    
            code_str = f.read()
        
        import_stmts.extend(get_all_imports(code_str)[2])
        get_all_calls(path, code_str, code_dependancies)
        
    else:
        raise Exception(f'Could not parse path: `{path}`')
        
                
    import_stmts = list(set(import_stmts))

    simple_funcs = [func_name for func_name in code_dependancies.keys() if code_dependancies.dependancies(func_name) == 0]

    logging.debug(f'Total functions/methods/clases: {len(code_dependancies.keys())}')

    known_docs = get_known_function_docs(import_stmts, simple_funcs)

    logging.info(f'Existing docs found for {len([x for x in known_docs if x != "-"])}/{len(code_dependancies.keys())} calls')

    n = len(simple_funcs)
    logging.info(f'Using `{args.ref_doc}` strategy to shorten docs')
    
    for i,(func,known_doc) in enumerate(zip(simple_funcs, known_docs)):
        if args.ref_doc == 'summarize' and (n <=10 or (i+1)%(round(n/10)) == 0):
            logging.info(f'\t[{i+1}/{n}] {round(100*(i+1)/n)}% done')

        code_dependancies.add(
            func, 
            {CodeData.DOC_SHORT: get_shortened_docs(func, known_doc, args.ref_doc)}
        )
                

    custom_funcs = [func_name for func_name, func_info in code_dependancies.items() if func_info[CodeData.CUSTOM]]

    n = len(custom_funcs)
    num_digits = math.ceil(math.log(n, 10))
    logging.info(f'Generating docs for {len(custom_funcs)} custom functions/methods/classes')

    for i in range(3):
        least_dep_func = min(custom_funcs, key=lambda x: code_dependancies.undocumented_dependancies(x))
        reason = None
        
        for ri in range(args.max_retries):
            llm_out = get_llm_output(
                SYSTEM_PROMPT, 
                DOC_GENERATION_PROMPT(
                    code_dependancies[least_dep_func][CodeData.CODE], 
                    get_reference_docs(least_dep_func, code_dependancies)
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
                logging.info(f'\t[{str(i+1).zfill(num_digits)}/{str(n).zfill(num_digits)}] Generated docs for `{least_dep_func}` in {ri+1}/{args.max_retries} tries')      
                break
            else:
                with open('debug.func.log', 'a') as f:
                    print(f'func: {least_dep_func} | try: {ri}', file=f)
                    print(new_func_code, file=f)
                    print('-'*10, file=f)
                    print(code_dependancies[least_dep_func][CodeData.CODE], file=f)
                    print('-'*42, file=f)
                reason = 'Generated AST does not match original AST'
        else:
            logging.info(f'\t[{str(i+1).zfill(num_digits)}/{str(n).zfill(num_digits)}] Could not generate docs for `{least_dep_func}` after {args.max_retries} tries (Reason: {reason})')
        
        if code_dependancies[least_dep_func][CodeData.DOC] != '-':
            code_dependancies.add(
                func, 
                {CodeData.DOC_SHORT: get_shortened_docs(func, CodeData.DOC, args.ref_doc)}
            )            

        custom_funcs.remove(least_dep_func)
        
    custom_funcs_with_docs = [func_name for func_name, func_info in code_dependancies.items() if func_info[CodeData.CUSTOM] and func_info[CodeData.DOC] != '-']
    logging.info(f'Generated docs for {len(custom_funcs_with_docs)}/{n} custom functions/classes')
    
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
    
    generate_report(code_dependancies, f'doc_report_{args.path.split("/")[-1]}.csv')
    logging.info(f'Saved Documentation report in ./doc_report_{args.path.split("/")[-1]}.csv')

if __name__ == '__main__':
    main()