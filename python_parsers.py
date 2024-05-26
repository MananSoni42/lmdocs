import ast
from collections import deque
from constants import FUNCS_TO_INGORE
import re
from itertools import zip_longest
from typing import Union
from get_function_docs import CodeData
import logging
import copy


def to_remove(func_str):
    for func in FUNCS_TO_INGORE:
        if func.lower().strip() == func_str.lower().strip() or re.fullmatch(f'[^\W0-9]\w*.{func}', func_str):
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


def get_all_funcs(path, funcs):
    with open(path) as f:    
        tree = ast.parse(f.read())
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                funcs.add(
                    node.name,
                    {
                        CodeData.CODE: ast.unparse(node),
                        CodeData.NODE: node,
                        CodeData.DEP: get_func_calls(node),
                        CodeData.CUSTOM: True,
                        CodeData.PATH: path,
                    }
                )


def get_all_imports(path):
    libs = []
    import_stmts = []
    alias_map = {}
    with open(path) as f:    
        tree = ast.parse(f.read())
        
        for node in ast.walk(tree):

            if isinstance(node, ast.Import):
                import_stmts.append(ast.unparse(node))
                for import_alias in node.names:
                    libs.append(import_alias.name)                        
                    if import_alias.asname: 
                        alias_map[import_alias.asname] = import_alias.name
            
            if isinstance(node, ast.ImportFrom):
                import_stmts.append(ast.unparse(node))
                module = node.module
                for import_alias in node.names:                    
                    libs.append(f'{module}.{import_alias.name}')                    
                    if import_alias.asname:                     
                        alias_map[import_alias.asname] = import_alias.name
                
                    
    return libs, alias_map, import_stmts


def parse_commented_function(func_name, func_str):
    try:
        func_str = func_str.split('```python')[1]
    except IndexError:
        func_str = func_str.split('```python')[0]
        
    func_str = func_str.split('```')[0]
    func_str = func_str.lstrip().strip()
    func_str = func_str.lstrip('\n').strip('\n')
    func_str = func_str.lstrip().strip()
    
    ast_func, success = '', False

    try:
        ast_func = ast.parse(func_str)
        success = True
    except Exception as e:
        logging.error(f'Could not parse function {func_name}: `{e}')
        
    if not isinstance(ast_func, ast.FunctionDef):
        for node in ast.walk(ast_func):
            if isinstance(node, ast.FunctionDef):
                ast_func = node
                break
            
    if not isinstance(ast_func, ast.FunctionDef):
        success = False
        
    return func_str, ast_func, success


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
