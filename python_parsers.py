import ast
from collections import deque
from pprint import pprint

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

    return list(set(func_calls))


def get_all_funcs(path):
    funcs = []
    with open(path) as f:    
        tree = ast.parse(f.read())
        
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                funcs.append((node.name, get_func_calls(node)))
    return funcs    


def get_all_imports(path):
    imports = []
    alias_map = {}
    with open(path) as f:    
        tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for import_alias in node.names:
                    imports.append(import_alias.name)                        
                    if import_alias.asname: 
                        alias_map[import_alias.asname] = import_alias.name
                    
            if isinstance(node, ast.ImportFrom):
                module = node.module
                for import_alias in node.names:                    
                    imports.append(f'{module}.{import_alias.name}')                    
                    if import_alias.asname:                     
                        alias_map[import_alias.asname] = import_alias.name
                    
    return imports, alias_map

# print(get_all_funcs('./movie_rec/collaborative_filtering.py'))
# print(get_all_imports('./movie_rec/collaborative_filtering.py'))

# pprint(get_all_imports('utils.py'))
pprint(get_all_funcs('utils.py'))