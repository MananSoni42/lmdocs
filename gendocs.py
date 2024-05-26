from python_parsers import get_all_funcs, get_all_imports, parse_commented_function, same_ast, remove_docstring
from get_function_docs import CodeData, get_known_function_docs, get_reference_docs, get_summarized_docs, get_truncated_docs
from prompts import SYSTEM_PROMPT, SUMMARIZE_DOC_PROMPT, FUNCTION_DOC_GENERATION_PROMPT
from constants import MAX_RETRIES
from local_llm_inference import get_local_llm_output
from utils import get_args, verify_args, generate_report

import ast
import os
import copy
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

def main():
    
    args = get_args()    
    
    path = args.path
    logging.info(f'Project path: {path}')

    import_stmts = []
    code_dependancies = CodeData()
    
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                if os.path.splitext(file)[-1] == '.py':
                    path = os.path.join(root, file)
                    logging.info(f'\tExtracting dependancies from {path}')
                    import_stmts.extend(get_all_imports(path)[2])
                    get_all_funcs(path, code_dependancies)
                    
    elif os.path.splitext(path)[-1] == '.py':
        logging.info(f'\tExtracting dependancies from {path}')
        import_stmts.extend(get_all_imports(path)[2])
        get_all_funcs(path, code_dependancies)
        
    else:
        raise Exception(f'Could not parse path: `{path}`')
        
                
    import_stmts = list(set(import_stmts))

    simple_funcs = [func_name for func_name in code_dependancies.keys() if code_dependancies.dependancies(func_name) == 0]

    logging.info(f'Total functions: {len(code_dependancies.keys())}')
    logging.info(f'Simple functions: {len(simple_funcs)}')

    known_docs = get_known_function_docs(import_stmts, simple_funcs)

    logging.info(f'Documentation found for {len([x for x in known_docs if x != "-"])} simple functions')

    n = len(simple_funcs)
    logging.info('Summarizing/Truncating known docs')
    for i,(func,known_doc) in enumerate(zip(simple_funcs, known_docs)):
        if n <=10 or (i+1)%(round(n/10)) == 0:
            logging.info(f'\t[{i+1}/{n}] {round(100*(i+1)/n)}% done')
        if known_docs != '-':
            code_dependancies.add(
                func, 
                # {CodeData.DOC: get_summarized_docs(func, known_doc)}
                {CodeData.DOC: get_truncated_docs(func, known_doc)}
            )

    custom_funcs = [func_name for func_name, func_info in code_dependancies.items() if func_info[CodeData.CUSTOM]]
    logging.info(f'Custom functions: {len(custom_funcs)}')

    n = len(custom_funcs)
    logging.info('Generating docs for custom functions')

    for i in range(n):
        least_dep_func = min(custom_funcs, key=lambda x: code_dependancies.undocumented_dependancies(x))
        
        for _ in range(MAX_RETRIES):
            llm_out = get_local_llm_output(SYSTEM_PROMPT, FUNCTION_DOC_GENERATION_PROMPT(code_dependancies[least_dep_func][CodeData.CODE], get_reference_docs(least_dep_func, code_dependancies)))
            new_func_code, new_func_node, success = parse_commented_function(least_dep_func, llm_out)
            
            if not success:
                continue
        
            if same_ast(code_dependancies[least_dep_func][CodeData.NODE], remove_docstring(new_func_node)):
                code_dependancies.add(
                    least_dep_func,
                    {
                        'code_updated': new_func_code,
                        CodeData.NODE: new_func_node,
                        CodeData.DOC: ast.get_docstring(new_func_node)
                    }
                )
                logging.info(f'\t[{i+1}/{n}] Added docs for function: `{least_dep_func}`')      
                break
        else:
            code_dependancies.add(
                    least_dep_func,
                    { 'code_updated': 'N/A' }
            )
            logging.info(f'\t[{i+1}/{n}] Could not add docs for function: `{least_dep_func}`')

        custom_funcs.remove(least_dep_func)
        
    logging.info('Generating Documentation  report')
    generate_report(code_dependancies, f'doc_report_{args.path.split("/")[-1]}.csv')

if __name__ == '__main__':
    main()