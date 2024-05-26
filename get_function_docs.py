import logging
from prompts import SYSTEM_PROMPT, SUMMARIZE_DOC_PROMPT
from local_llm_inference import get_local_llm_output

class CodeData:
    
    DEP = 'dependances'
    DOC = 'documentation'
    CODE = 'code'
    NODE = 'node'
    CUSTOM = 'custom'
    PATH = 'path'
    
    def __init__(self):
        self.funcs = {}
        self.DEFAULT_OUTPUT = {
            CodeData.DEP: [], 
            CodeData.DOC: '-',
            CodeData.NODE: None, 
            CodeData.CODE: '-', 
            CodeData.CUSTOM: False,
            CodeData.PATH: '-',
        }
        
    def __getitem__(self, name):
        return self.funcs.get(name, self.DEFAULT_OUTPUT.copy())
    
    def add(self, name, data):
        if name not in self.funcs:
            self.funcs[name] = self.DEFAULT_OUTPUT.copy()
        
        for k,v in data.items():
            self.funcs[name][k] = v
        
            if k == CodeData.DEP:
                for func in v:
                    self.add(func, {CodeData.DEP: [], CodeData.PATH: data.get(CodeData.PATH, '-')})
                 
    def dependancies(self, name):
        fobj = self.funcs.get(name, {})
        return len(fobj.get(CodeData.DEP, []))
    
    def documented_dependancies(self, name):
        fobj = self.funcs.get(name, {})
        return len([f for f in fobj.get(CodeData.DEP, []) if self.__getitem__(f)[CodeData.DOC]])
            
    def undocumented_dependancies(self, name):
        fobj = self.funcs.get(name, {})
        return len([f for f in fobj.get(CodeData.DEP, []) if not self.__getitem__(f)[CodeData.DOC]])

    def items(self):
        return self.funcs.items()

    def keys(self):
        return self.funcs.keys()

    def values(self):
        return self.funcs.values()
    
    def __str__(self):
        out_str = ''
        for func,func_info in self.funcs.items():
            out_str += f'Function: {func} (Custom: {func_info[CodeData.CUSTOM]}), Dependancies: {self.dependancies(func)}, Documented Dependancies: {self.documented_dependancies(func)}\n'
        return out_str

    def __repr__(self):
        return self.__str__()


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
            logging.debug(f'Could not import using the statement: `{stmt}`')
            
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
            logging.debug(f'No documentation found for func: {func}')
    
    return docs


def get_reference_docs(func, code_dependancies):
    ref_docs = []
    for dep_func in code_dependancies[func][CodeData.DEP]:
        if code_dependancies[dep_func][CodeData.DOC] != '-':
            ref_docs.append({
                'function': dep_func,
                'doc_str': code_dependancies[dep_func][CodeData.DOC]
            })
    return ref_docs


def get_summarized_docs(func_name, doc_str):
   return get_local_llm_output(SYSTEM_PROMPT, SUMMARIZE_DOC_PROMPT(func_name, doc_str))


def get_truncated_docs(func_name, doc_str):
    trunc_doc_str = doc_str.split('\n\n')[0]
    if len(trunc_doc_str) == len(doc_str):
        trunc_doc_str = doc_str.split('\n')[0]
        
    logging.debug(f'Truncated doc for {func_name} from {len(doc_str)} to {len(trunc_doc_str)}')
        
    return trunc_doc_str