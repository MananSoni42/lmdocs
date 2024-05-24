import pandas as pd


def clean_doc_str(doc_str):
    doc_str = doc_str.strip()
    doc_str = doc_str.lstrip('\n')
    doc_str = doc_str.rstrip('\n')
    return doc_str
    
    
def get_known_function_docs(import_stmts, funcs):
    for stmt in import_stmts:
        try:
            exec(stmt)
        except ImportError:
            print(f'Could not import using the statement: `{stmt}`')
            
    docs = []
    for func in funcs:
        func_doc = '-'
        func_parts = func.split('.')
        for i in range(len(func_parts)):
            subfunc = '.'.join(func_parts[i:])
            try:
                func_doc = clean_doc_str(eval(f'{subfunc}.__doc__'))
                break
            except:
                pass
        
        docs.append(func_doc)
        if func_doc == '-':
            print(f'No documentation found for func: {func}')
    
    return docs


def make_func_df(funcs):
    func_data = []
    all_funcs = list({subfunc for (func_def, func_info) in funcs.items() for subfunc in [func_def] + list(func_info['dependancies'])})
    for func in all_funcs:
        func_data.append({
                'function_name': func.split('.')[-1],        
                'full_function_name': func,
                'dependancies': funcs.get(func, {}).get('dependancies', []),
            }
        )
    return pd.DataFrame(func_data)


def get_reference_docs(func, func_df):
    func_deps = set(func_df[func_df.function_name == func].iloc[0].dependancies)
    ref_docs = []
    for _,row in func_df.iterrows():
        if row.full_function_name in func_deps and row.known_doc_summary != '-':
            ref_docs.append({
                'function': row.function_name,
                'doc_str': row.known_doc_summary
            })
    return ref_docs
