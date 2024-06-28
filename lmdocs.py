from get_code_docs import CodeData, get_reference_docs_simple_functions, get_reference_docs_custom_functions, get_shortened_docs
from constants import LOCAL, OPENAI
from llm_inference import get_local_llm_name
from utils import get_args, generate_report, get_code_dependancies_and_imports, generate_documentation_for_custom_calls, replace_modified_functions

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)    
    
def main():
    
    args = get_args()    
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    logging.info(f'Project path: {args.path}')
    
    llm_mode = LOCAL if args.port else OPENAI
    model_name = get_local_llm_name(args.port) if llm_mode == LOCAL else args.openai_model
    logging.info(f'Using {llm_mode} LLM: {model_name}')
    
    code_dependancies, import_stmts = get_code_dependancies_and_imports(args.path)
    logging.debug(f'Found {len(code_dependancies.keys())} functions/methods/clases: ')

    simple_funcs = [func_name for func_name in code_dependancies.keys() if code_dependancies.dependancies(func_name) == 0]
    reference_docs = get_reference_docs_simple_functions(import_stmts, simple_funcs)
    logging.info(f'Reference documentation found for {len([x for x in reference_docs if x != "-"])}/{len(code_dependancies.keys())} calls')

    num_simple_funcs = len(simple_funcs)
    logging.info(f'Using `{args.ref_doc}` strategy to shorten docs')
    
    for i,(func,known_doc) in enumerate(zip(simple_funcs, reference_docs)):
        if args.ref_doc == 'summarize' and (num_simple_funcs <=10 or (i+1)%(round(num_simple_funcs/10)) == 0):
            logging.info(f'\t[{i+1}/{num_simple_funcs}] {round(100*(i+1)/num_simple_funcs)}% done')

        code_dependancies.add(
            func, 
            {CodeData.DOC_SHORT: get_shortened_docs(func, known_doc, args.ref_doc, llm_mode, args)}
        )
        
    generate_documentation_for_custom_calls(code_dependancies, llm_mode, args)

    replace_modified_functions(code_dependancies, args.path)
    
    generate_report(code_dependancies, f'doc_report_{args.path.split("/")[-1]}.csv')
    logging.info(f'Saved Documentation report in ./doc_report_{args.path.split("/")[-1]}.csv')


if __name__ == '__main__':
    main()