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
import subprocess
import sys


def to_remove(call_str):
    """
    Determines if a given call string should be removed based on specific criteria.

    Input:
        call_str (str): The call string to be checked.

    Returns:
        bool: True if the call string matches any criteria for removal, False otherwise.

    Raises:
        None

    """
    for call in CALLS_TO_INGORE:
        # Check if call string matches any ignored call strings (case insensitive)
        if call.lower().strip() == call_str.lower().strip() or re.fullmatch(f'[^\W0-9]\w*.{call}', call_str):
            return True
    return False


class FuncCallVisitor(ast.NodeVisitor):
    def __init__(self):
        """
        Initializes an instance of the class.
    
        This method sets up the class by initializing the `_name` attribute
        as an empty deque object.
    
        Input: None
    
        Returns: None
    
        Raises: None
        """
        self._name = deque()  # Initialize the _name attribute as an empty deque

    @property
    def name(self):
        return '.'.join(self._name)

    @name.deleter
    def name(self):
        self._name.clear()

    def visit_Name(self, node):
        """
        Visit a node representing a name and prepend the node's ID to the internal _name deque.
    
        Input: 
        - node: The node whose name (ID) is to be visited and appended.
    
        Returns: 
        None
    
        Raises: 
        No exceptions are explicitly raised by this function.
        """
        self._name.appendleft(node.id)  # Prepend the node's ID to the _name deque

    def visit_Attribute(self, node):
        """
        Visit an attribute node in the abstract syntax tree (AST).
    
        This function processes an attribute node and attempts to extract and prepend the attribute name
        and the value's identifier to the _name deque. If the 'value' attribute does not have an 'id', 
        it falls back to a generic visit.
    
        Input:
            node: The AST node representing the attribute.
    
        Returns:
            None
    
        Raises:
            AttributeError: If the 'node.value' does not have an 'id' attribute.
        """
        try:
            self._name.appendleft(node.attr)
            self._name.appendleft(node.value.id)
        except AttributeError:
            self.generic_visit(node)
           
 
def get_func_calls(tree):
    """
    Extract and return a list of unique function call names from an abstract syntax tree (AST).

    Input:
    tree: The root node of the AST to traverse.

    Returns:
    A list of unique function names called within the AST.

    Raises:
    No specific exceptions are raised, but the function assumes that `tree` is a valid AST node.
    """
    func_calls = []
    for node in ast.walk(tree):  # Iterate through all nodes in the AST
        if isinstance(node, ast.Call):  # Check if the node is a function call
            callvisitor = FuncCallVisitor()
            callvisitor.visit(node.func)
            func_calls.append((callvisitor.name))

    func_calls = list(set(func_calls))  # Remove duplicate function names
    func_calls = [func for func in func_calls if not to_remove(func)]  # Filter out functions that need to be removed

    return func_calls


def get_all_calls(path, code_str, funcs):
    """
    Extracts all function and method calls from the given Python code string and adds them to a provided data structure.

    Input:
        path (str): The file path from which the code string was read.
        code_str (str): The string containing Python code to be parsed.
        funcs (object): A data structure (e.g., dictionary or custom object) to store information about the functions and methods extracted.

    Returns:
        None: This function updates the `funcs` data structure in place.

    Raises:
        SyntaxError: If the provided `code_str` is not valid Python code.
    """
    
    tree = ast.parse(code_str)  # Parse the source code into an AST node

    for node in tree.body:  # Iterate over the top-level nodes in the AST
        
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef):  # Check if the node is a function or class definition
            
            extra_deps = []
            if isinstance(node, ast.ClassDef):  # If the node is a class definition
                for child_node in node.body:  # Iterate over the child nodes in the class body
                    if isinstance(child_node, ast.FunctionDef):  # Check if the child node is a function definition
                        extra_deps.append(child_node.name)
                        funcs.add(
                            child_node.name,
                            {
                                CodeData.CODE: ast.get_source_segment(code_str, child_node),  # Get the source segment for the child function
                                CodeData.NODE: child_node,
                                CodeData.DEP: get_func_calls(child_node),  # Get function calls within the child function
                                CodeData.CUSTOM: True,
                                CodeData.PATH: path,
                                CodeData.CODE_INDENT: get_indent_from_file(path),  # Get the code indentation level from the file
                                CodeData.TYPE: 'method',
                            }
                        )

            funcs.add(
                node.name,
                {
                    CodeData.CODE: ast.get_source_segment(code_str, node),  # Get the source segment for the function or class
                    CodeData.NODE: node,
                    CodeData.DEP: get_func_calls(node),  # Get function calls within the function or class
                    CodeData.CUSTOM: True,
                    CodeData.PATH: path,
                    CodeData.TYPE: 'function' if isinstance(node, ast.FunctionDef) else 'class',
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
                    CodeData.TYPE: 'function' if isinstance(node, ast.FunctionDef) else 'class',
                }
            )


def get_all_imports(code_str):
    """
    Extract all import statements and their details from the given Python code string.

    Input:
    code_str (str): The Python code as a string from which to extract import statements.

    Returns:
    tuple:
        - libs (list of str): List of library names imported in the code.
        - alias_map (dict): Mapping of alias names to their respective original library names.
        - import_stmts (list of str): List of the actual import statements found in the code.

    Raises:
    None
    """
    libs = []
    import_stmts = []
    alias_map = {}

    # Parse the source code into an AST node
    tree = ast.parse(code_str)
        
    # Walk through all nodes of the AST
    for node in ast.walk(tree):
        
        # If the node is an import statement
        if isinstance(node, ast.Import):
            import_stmts.append(ast.get_source_segment(code_str, node))
            for import_alias in node.names:
                libs.append(import_alias.name)
                if import_alias.asname:
                    alias_map[import_alias.asname] = import_alias.name
        
        # If the node is a 'from ... import ...' statement
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
        reason = f'Parse error `({repr(e)[:50]}...)`' 
        
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
    """
    Remove the docstring from an AST function node.

    Input:
    func_node (ast.FunctionDef): The function node from which the docstring should be removed.

    Returns:
    ast.FunctionDef: A deep copy of the input function node with the docstring removed.

    Raises:
    TypeError: If the input is not an instance of ast.FunctionDef.
    """
    
    # Create a deep copy of the function node to avoid mutating the original node
    func_node_copy = copy.deepcopy(func_node)
    
    # Filter out the docstring from the body of the node
    func_node_copy.body = [node for node in func_node_copy.body 
                           if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))]
    
    return func_node_copy
   
    
def same_ast(node1: Union[ast.expr, list[ast.expr]], node2: Union[ast.expr, list[ast.expr]]) -> bool:
    """
    Compare two AST nodes for structural equality.

    Args:
        node1 (Union[ast.expr, list[ast.expr]]): The first AST node or list of AST nodes to compare.
        node2 (Union[ast.expr, list[ast.expr]]): The second AST node or list of AST nodes to compare.

    Returns:
        bool: True if the AST nodes are structurally equal, False otherwise.

    Raises:
        None
    """
    
    if type(node1) is not type(node2):
        # If the types of nodes are not the same, they cannot be equal
        return False

    if isinstance(node1, ast.AST):
        # Compare all attributes of the AST nodes, ignoring specific attributes
        for k, v in vars(node1).items():
            if k in {"lineno", "end_lineno", "col_offset", "end_col_offset", "ctx"}:
                continue  # Ignore attributes related to position and context
            if not same_ast(v, getattr(node2, k)):
                return False
        return True

    elif isinstance(node1, list) and isinstance(node2, list):
        # Compare lists of AST nodes
        return all(same_ast(n1, n2) for n1, n2 in zip_longest(node1, node2))
    else:
        # For other types, use direct comparison
        return node1 == node2


def same_ast_with_reason(node1: Union[ast.expr, list[ast.expr]], node2: Union[ast.expr, list[ast.expr]], parent=None) -> tuple[bool, str]:
    """
    Compare two AST nodes or lists of AST nodes for structural equivalence and provide a reason if they differ.

    Input:
    node1: Union[ast.expr, list[ast.expr]]
        The first AST node or list of AST nodes to compare.
    node2: Union[ast.expr, list[ast.expr]]
        The second AST node or list of AST nodes to compare.
    parent: Optional
        The parent node used to provide more context in the reason for differences.

    Returns:
    tuple[bool, str]
        A tuple containing a boolean indicating whether the nodes are the same (True) or not (False), and a string providing the reason if they are not the same.

    Raises:
    TypeError
        If the types of node1 and node2 are not the same.
    """
    
    if type(node1) is not type(node2):
        if parent:
            return False, f'`[TYPE] `{type(parent)}.{type(node1)}` != `{type(parent)}.{type(node2)}`'
        else:
            return False, f'`[TYPE] `{type(node1)}` != `{type(node2)}`'
        
    if isinstance(node1, ast.AST):
        for k, v in vars(node1).items():
            if k in {"lineno", "end_lineno", "col_offset", "end_col_offset", "ctx"}:
                continue
            same, reason = same_ast_with_reason(v, getattr(node2, k), node2)
            if not same:
                return False, reason
        return True, 'Same AST'

    elif isinstance(node1, list) and isinstance(node2, list):
        for n1, n2 in zip_longest(node1, node2):
            same, reason = same_ast_with_reason(n1, n2, node2)
            if not same:
                return False, reason
        return True, 'Same AST'
    else:
        if node1 == node2:
            return True, 'Same AST'
        else:
            if parent:
                return False, f'[NODE] `{type(parent)}.{type(node1)}` (`{node1}`) != `{type(parent)}.{type(node2)}` (`{node2}`)'
            else:
                return False, f'[NODE] `{type(node1)}` (`{node1}`) != `{type(node2)}` (`{node2}`)'

def remove_comments_from_line(line):
    """
    Remove comments from a given line of code.

    Input:
    - line (str): A single line of code which may contain comments starting with '#'.

    Returns:
    - str: The line of code with the comments removed.

    Raises:
    - None
    """
    # Use regular expression to find and remove comments from the line
    return re.sub('#+[\s]*.*\n*$', '', line)


py_clean = lambda x: remove_comments_from_line(x.lstrip('\t').strip()).lstrip('\t').strip()

empty_line = lambda x: False if x.replace('\n', '').replace('\t', '').strip() else True

clean_code_lines = lambda clines: [(i,py_clean(cline)) for i,cline in enumerate(clines) if not empty_line(py_clean(cline))]


def replace_func_single_line(func_name, orig_code_lines, new_code_lines, file_path, flines):
    """
    Replaces a function definition in a file with new code lines.

    Input:
    - func_name (str): The name of the function to be replaced.
    - orig_code_lines (list): The original code lines of the function.
    - new_code_lines (list): The new code lines to replace the original function.
    - file_path (str): The path to the file where the function resides.
    - flines (list): The lines of the file where the function resides.

    Returns:
    - new_flines (list): The updated lines of the file after the function has been replaced.

    Raises:
    - Logs an error if the function cannot be found and replaced in the specified file.
    """

    cleaned_orig_code_lines = clean_code_lines(orig_code_lines)
    cleaned_flines = clean_code_lines(flines)
    
    first_line, last_line = cleaned_orig_code_lines[0][1], cleaned_orig_code_lines[-1][1]
    
    start_ind, end_ind = -1, -1
    for (ind,fline) in cleaned_flines:        
        # Find the start index of the function's first line
        if fline == first_line:
            start_ind = ind
        # Find the end index of the function's last line
        if start_ind != -1 and fline == last_line:
            end_ind = ind
            break
        
    if start_ind == -1 or end_ind == -1:
        # Log an error if the function's start or end couldn't be found
        logging.error(f'Could not replace `{func_name}` in file `{file_path} (Start: {start_ind}, End: {end_ind})')
        new_flines = flines
    else:
        # Replace the function's lines in the file
        new_flines = flines[:start_ind] + new_code_lines + flines[end_ind+1:]
        
    return new_flines


def replace_func_double_line(func_name, orig_code_lines, new_code_lines, file_path, flines):
    """
    Replace specific lines of a function in a file with new lines of code.

    Input:
        func_name (str): The name of the function to be replaced.
        orig_code_lines (list): List of tuples where each tuple contains an index and a line of code from the original function.
        new_code_lines (list): List of new code lines to replace the original function lines.
        file_path (str): The file path where the function is located.
        flines (list): List of tuples where each tuple contains an index and a line of code from the file.

    Returns:
        new_flines (list): The file lines after replacing the necessary function lines with new code lines.

    Raises:
        Logs an error if the function lines to be replaced cannot be found in the file.
    """
            
    cleaned_orig_code_lines = clean_code_lines(orig_code_lines)
    cleaned_flines = clean_code_lines(flines)
    
    # Extract the first, second last, and last line of the function to be replaced
    first_line, second_last_line, last_line = cleaned_orig_code_lines[0][1], cleaned_orig_code_lines[-2][1], cleaned_orig_code_lines[-1][1]
    
    start_ind, end_ind = -1, -1
    n = len(cleaned_flines)
    for i in range(n-1):
        ind, fline = cleaned_flines[i]
        ind_next, fline_next = cleaned_flines[i+1]
        
        if fline == first_line:
            start_ind = ind  # Detecting the start of the function
        if start_ind != -1 and fline == second_last_line and fline_next == last_line:
            end_ind = ind_next  # Detecting the end of the function
            break
        
    if start_ind == -1 or end_ind == -1:
        logging.error(f'Could not replace `{func_name}` in file `{file_path} (Start: {start_ind}, End: {end_ind})')
        new_flines = flines  # If the function is not found, retain the original file lines
    else:
        new_flines = flines[:start_ind] + new_code_lines + flines[end_ind+1:]  # Replace the function lines with new lines
        
    return new_flines


def replace_func(func_name, orig_code_str, new_code_str, file_path, f_str):
    """
    Replace a function's code in a file with new code.
    
    Input:
    - func_name: The name of the function to be replaced.
    - orig_code_str: The original code of the function as a string.
    - new_code_str: The new code to replace the original code with as a string.
    - file_path: The path to the file containing the function.
    - f_str: The entire content of the file as a single string.
    
    Returns:
    - A string representing the entire content of the file with the function replaced.
    
    Raises:
    - This function does not raise any exceptions directly but relies on sub-functions that might raise exceptions.
    """
    
    orig_code_lines = orig_code_str.split('\n')
    new_code_lines = new_code_str.split('\n')
    num_code_lines = len(orig_code_lines)
    flines = f_str.split('\n')
    
    if num_code_lines <= 2:
        # Handle replacement for functions with only one or two lines of code
        return '\n'.join(replace_func_single_line(func_name, orig_code_lines, new_code_lines, file_path, flines))
    else:
        # Handle replacement for functions with more than two lines of code
        return '\n'.join(replace_func_double_line(func_name, orig_code_lines, new_code_lines, file_path, flines))


def get_indent_from_file(path):
    """
    Retrieve the indentation string from a Python source file.

    Input:
    - path (str): The path to the Python source file.

    Returns:
    - str: The string used for indentation (tabs or spaces) in the file.

    Raises:
    - Logs an error if no indentation is found in the file.
    """
    with open(path) as f:
        for (tok_type, tok_str, _, _, _) in tokenize.generate_tokens(f.readline):
            if tok_type == tokenize.INDENT:
                return tok_str  # Return the indentation string if found
    logging.error(f'Could not find indent (tabs/spaces) from path: `{path}`')  # Log an error if indentation is not found