from python_parsers import get_all_funcs, get_all_imports
from get_function_docs import make_func_df, get_known_function_docs, get_reference_docs
from prompts import SYSTEM_PROMPT, SUMMARIZE_DOC_PROMPT, FUNCTION_DOC_GENERATION_PROMPT
from local_llm_inference import get_local_llm_output

import os
from tqdm import tqdm

project_path = 'movie_rec'

print(project_path)

import_stmts = []
funcs = {}
for root, dirs, files in os.walk(project_path):
    for file in files:
        if os.path.splitext(file)[-1] == '.py':
            path = os.path.join(root, file)
            import_stmts.extend(get_all_imports(path)[2])
            funcs = funcs | get_all_funcs(path)
            
import_stmts = list(set(import_stmts))
func2str = {func: func_info['function_str'] for func, func_info in funcs.items()}

df = make_func_df(funcs)

df['known_docs'] = get_known_function_docs(import_stmts, [row.full_function_name for _,row in df.iterrows()])
df['known_doc_summary'] = [
    get_local_llm_output(SYSTEM_PROMPT, SUMMARIZE_DOC_PROMPT(row.function_name, row.known_docs)) if row.known_docs != '-' else '-'
    for _, row in tqdm(df.iterrows(), total=df.shape[0], desc='summarize known docs')
]

df['unknown_docs'] = [
    get_local_llm_output(SYSTEM_PROMPT, FUNCTION_DOC_GENERATION_PROMPT(func2str[row.function_name], get_reference_docs(row.function_name, df))) \
    if row.dependancies != [] else '-'
    for _, row in tqdm(df.iterrows(), total=df.shape[0], desc='generate new docs')
]

df.to_excel(f'./dep_graph_{project_path}.xlsx', index=False)