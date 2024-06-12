import ast
from collections import deque
from constants import CALLS_TO_INGORE
import re
from itertools import zip_longest
from typing import Union
from get_code_docs import CodeData
import logging
import tokenize
import copy


def to_remove(call_str):
    for call in CALLS_TO_INGORE:
        if call.lower().strip() == call_str.lower().strip() or re.fullmatch(f'[^\W0-9]\w*.{call}', call_str):
            return True
    return False


class FuncCallVisitor(ast.NodeVisitor):
    def __init__(self):
        self._name = deque()

    @property
    def name(self):
        return '.'.join(self._name)

    @name.deleter
    def name(self):
        self._name.clear()

    def visit_Name(self, node):
        self._name.appendleft(node.id)

    def visit_Attribute(self, node):
        try:
            self._name.appendleft(node.attr)
            self._name.appendleft(node.value.id)
        except AttributeError:
            self.generic_visit(node)
           
 
def get_func_calls(tree):
    func_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            callvisitor = FuncCallVisitor()
            callvisitor.visit(node.func)
            func_calls.append((callvisitor.name))

    func_calls = list(set(func_calls))
    func_calls = [func for func in func_calls if not to_remove(func)]

    return func_calls


def get_all_calls(path, code_str, funcs):    
    tree = ast.parse(code_str)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef):

            extra_deps = []
            if isinstance(node, ast.ClassDef):
                for child_node in node.body:
                    if isinstance(child_node, ast.FunctionDef):
                        extra_deps.append(child_node.name)
                        funcs.add(
                            child_node.name,
                            {
                                CodeData.CODE: ast.get_source_segment(code_str, child_node),
                                CodeData.NODE: child_node,
                                CodeData.DEP: get_func_calls(child_node),
                                CodeData.CUSTOM: True,
                                CodeData.PATH: path,
                                CodeData.CODE_INDENT: get_indent_from_file(path),
                            }
                        )

            funcs.add(
                node.name,
                {
                    CodeData.CODE: ast.get_source_segment(code_str, node),
                    CodeData.NODE: node,
                    CodeData.DEP: get_func_calls(node),
                    CodeData.CUSTOM: True,
                    CodeData.PATH: path,
                }
            )


def get_all_imports(code_str):
    libs = []
    import_stmts = []
    alias_map = {}
    
    tree = ast.parse(code_str)
        
    for node in ast.walk(tree):

        if isinstance(node, ast.Import):
            import_stmts.append(ast.get_source_segment(code_str, node))
            for import_alias in node.names:
                libs.append(import_alias.name)                        
                if import_alias.asname: 
                    alias_map[import_alias.asname] = import_alias.name
        
        if isinstance(node, ast.ImportFrom):
            import_stmts.append(ast.get_source_segment(code_str, node))
            module = node.module
            for import_alias in node.names:                    
                libs.append(f'{module}.{import_alias.name}')                    
                if import_alias.asname:                     
                    alias_map[import_alias.asname] = import_alias.name
                
                    
    return libs, alias_map, import_stmts


def parse_commented_function(func_name, func_str):
    
    clean_func = lambda x: x.lstrip().strip().lstrip('\n').strip('\n').lstrip().strip()
    
    if '```python' in func_str:
        func_str = func_str.split('```python')[1]
        
    func_str = func_str.strip('```')
    func_str = func_str.split('```\n')[0]
    func_str = clean_func(func_str)
    
    ast_code, success, reason = None, False, None

    try:
        ast_code = ast.parse(func_str)
        success = True
    except Exception as e:
        reason = f'Parse error `({repr(e)[:15]}...)`' 
        
    if ast_code and not (isinstance(ast_code, ast.FunctionDef) or isinstance(ast_code, ast.ClassDef)):
        for node in ast_code.body:
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef): 
                ast_code = node
                break
            
    if ast_code:
        _, _, import_stmts = get_all_imports(func_str)
        if import_stmts:
            logging.debug(f'\t\tRemoving import statements from generated version of `{func_name}`: {import_stmts}')
    
        for stmt in import_stmts:
            func_str = func_str.replace(stmt, '')
            func_str = clean_func(func_str)            
            
    if  ast_code and not (isinstance(ast_code, ast.FunctionDef) or isinstance(ast_code, ast.ClassDef)):
        success = False
        reason = f'Type error `({type(ast_code)})`'         
        
    return func_str, ast_code, success, reason


def remove_docstring(func_node):    
    func_node_copy = copy.deepcopy(func_node)
    func_node_copy.body = [node for node in func_node_copy.body if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))]
    return func_node_copy
   
    
def same_ast(node1: Union[ast.expr, list[ast.expr]], node2: Union[ast.expr, list[ast.expr]]) -> bool:
    
    if type(node1) is not type(node2):
        return False

    if isinstance(node1, ast.AST):
        for k, v in vars(node1).items():
            if k in {"lineno", "end_lineno", "col_offset", "end_col_offset", "ctx"}:
                continue
            if not same_ast(v, getattr(node2, k)):
                return False
        return True

    elif isinstance(node1, list) and isinstance(node2, list):
        return all(same_ast(n1, n2) for n1, n2 in zip_longest(node1, node2))
    else:
        return node1 == node2


py_clean = lambda x: x.lstrip('\t').strip()

empty_line = lambda x: False if x.replace('\n', '').replace('\t', '').strip() else True

clean_code_lines = lambda clines: [(i,py_clean(cline)) for i,cline in enumerate(clines) if not empty_line(cline)]

def replace_func_single_line(func_name, orig_code_lines, new_code_lines, file_path, flines):
    
    cleaned_orig_code_lines = clean_code_lines(orig_code_lines)
    cleaned_flines = clean_code_lines(flines)
    
    first_line, last_line = cleaned_orig_code_lines[0][1], cleaned_orig_code_lines[-1][1]
    # print('--->', first_line, last_line, sep='\n\t')
    
    start_ind, end_ind = -1, -1
    for (ind,fline) in cleaned_flines:        

        # print('---', fline)
        # print()
        
        if fline == first_line:
            start_ind = ind
        if start_ind != -1 and fline == last_line:
            end_ind = ind
            break
        
    if start_ind == -1 or end_ind == -1:
        logging.error(f'Could not replace `{func_name}` in file `{file_path} (Start: {start_ind}, End: {end_ind})')
        new_flines = flines
    else:
        new_flines = flines[:start_ind] + new_code_lines + flines[end_ind+1:]
        
    return new_flines


def replace_func_double_line(func_name, orig_code_lines, new_code_lines, file_path, flines):
            
    cleaned_orig_code_lines = clean_code_lines(orig_code_lines)
    cleaned_flines = clean_code_lines(flines)
    
    first_line, second_last_line, last_line = cleaned_orig_code_lines[0][1], cleaned_orig_code_lines[-2][1], cleaned_orig_code_lines[-1][1]
    
    start_ind, end_ind = -1, -1
    n = len(cleaned_flines)
    for i in range(n-1):
        ind, fline = cleaned_flines[i]
        ind_next, fline_next = cleaned_flines[i+1]
        
        if fline == first_line:
            start_ind = ind
        if start_ind != -1 and fline == second_last_line and fline_next == last_line:
            end_ind = ind_next
            break
        
    if start_ind == -1 or end_ind == -1:
        logging.error(f'Could not replace `{func_name}` in file `{file_path} (Start: {start_ind}, End: {end_ind})')
        new_flines = flines
    else:
        new_flines = flines[:start_ind] + new_code_lines + flines[end_ind+1:]
        
    return new_flines


def replace_func(func_name, orig_code_str, new_code_str, file_path, f_str):
    
    orig_code_lines = orig_code_str.split('\n')
    new_code_lines = new_code_str.split('\n')
    num_code_lines = len(orig_code_lines)
    flines = f_str.split('\n')
    
    if num_code_lines <= 2:
        return '\n'.join(replace_func_single_line(func_name, orig_code_lines, new_code_lines, file_path, flines))
    else:
        return '\n'.join(replace_func_double_line(func_name, orig_code_lines, new_code_lines, file_path, flines))

def get_indent_from_file(path):
    with open(path) as f:
        for (tok_type, tok_str, _, _, _) in tokenize.generate_tokens(f.readline):
            if tok_type == tokenize.INDENT:
                return tok_str
    logging.error(f'Could not find indent (tabs/spaces) from path: `{path}`')