import ast
from collections import deque
from constants import FUNCS_TO_INGORE
import re

def to_remove(func_str):
    for func in FUNCS_TO_INGORE:
        if re.fullmatch(func, func_str):
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


def get_all_funcs(path):
    funcs = {}
    with open(path) as f:    
        tree = ast.parse(f.read())
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                funcs[node.name] = {
                    'function_str': ast.unparse(node),
                    'dependancies': get_func_calls(node),
                }
                
    return funcs    


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
