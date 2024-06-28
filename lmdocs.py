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
    """
    Main function to generate documentation for code dependencies and custom calls.

    Input:
        None

    Returns:
        None

    Raises:
        Any exception raised during the execution will be logged, but none explicitly handled.
    """
    args = get_args()  # Get command-line arguments

    if args.verbose:
        # Set logging level to DEBUG if verbose flag is set
        logging.getLogger().setLevel(logging.DEBUG)

    logging.info(f'Project path: {args.path}')  # Log the project path

    # Determine the language model mode (local or OpenAI)
    llm_mode = LOCAL if args.port else OPENAI
    model_name = get_local_llm_name(args.port) if llm_mode == LOCAL else args.openai_model
    logging.info(f'Using {llm_mode} LLM: {model_name}')  # Log the LLM being used

    # Get code dependencies and import statements from the specified path
    code_dependancies, import_stmts = get_code_dependancies_and_imports(args.path)
    logging.debug(f'Found {len(code_dependancies.keys())} functions/methods/clases: ')

    # Identify simple functions with no dependencies
    simple_funcs = [func_name for func_name in code_dependancies.keys() if code_dependancies.dependancies(func_name) == 0]
    reference_docs = get_reference_docs_simple_functions(import_stmts, simple_funcs)
    logging.info(f'Reference documentation found for {len([x for x in reference_docs if x != "-"])}/{len(code_dependancies.keys())} calls')

    num_simple_funcs = len(simple_funcs)  # Number of simple functions
    logging.info(f'Using `{args.ref_doc}` strategy to shorten docs')

    # Process each simple function and add shortened documentation
    for i, (func, known_doc) in enumerate(zip(simple_funcs, reference_docs)):
        if args.ref_doc == 'summarize' and (num_simple_funcs <= 10 or (i + 1) % (round(num_simple_funcs / 10)) == 0):
            logging.info(f'\t[{i+1}/{num_simple_funcs}] {round(100*(i+1)/num_simple_funcs)}% done')

        code_dependancies.add(
            func,
            {CodeData.DOC_SHORT: get_shortened_docs(func, known_doc, args.ref_doc, llm_mode, args)}
        )

    # Generate documentation for custom calls
    generate_documentation_for_custom_calls(code_dependancies, llm_mode, args)

    # Replace the modified functions in the original code
    replace_modified_functions(code_dependancies, args.path)

    # Generate a report and save it as a CSV file
    generate_report(code_dependancies, f'doc_report_{args.path.split("/")[-1]}.csv')
    logging.info(f'Saved Documentation report in ./doc_report_{args.path.split("/")[-1]}.csv')


if __name__ == '__main__':
    main()