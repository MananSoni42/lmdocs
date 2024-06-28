import logging
from prompts import SYSTEM_PROMPT, DOC_SUMMARIZATION_PROMPT
from llm_inference import get_llm_output

class CodeData:
    
    DEP = 'dependances'
    DOC = 'documentation'
    DOC_SHORT = 'documentation_short'
    CODE = 'code'
    CODE_NEW = 'code_new'
    CODE_INDENT = 'code_indent'
    NODE = 'node'
    CUSTOM = 'custom'
    PATH = 'path'
    TYPE = 'code_type'
    
    def __init__(self):
        self.code_blobs = {}
        self.DEFAULT_OUTPUT = {
            CodeData.DEP: [], 
            CodeData.DOC: '-',
            CodeData.DOC_SHORT: '-',
            CodeData.NODE: None, 
            CodeData.CODE: '-',
            CodeData.CODE_NEW: '-',
            CodeData.CUSTOM: False,
            CodeData.PATH: '-',
            CodeData.CODE_INDENT: '',
            CodeData.TYPE: '??',
        }
        
    def __getitem__(self, name):
        """
        Retrieve a code blob by name or return a default output if not found.
    
        Input:
        - name (str): The name of the code blob to retrieve.
    
        Returns:
        - dict: The code blob associated with the specified name, or a copy of the default output if the name is not found.
    
        Raises:
        - KeyError: If the name is not found in the code blobs and the default output is not available for copying.
        """
        return self.code_blobs.get(name, self.DEFAULT_OUTPUT.copy())
    
    def add(self, name, data):
        """
        Adds a new code blob or updates an existing one with the provided data.
    
        Input:
            name: The name of the code blob to add or update.
            data: A dictionary containing the code blob data. The keys can be any attributes, including dependencies (CodeData.DEP).
    
        Returns:
            None
    
        Raises:
            KeyError: If a required key is missing from the data dictionary.
        """
        
        if name not in self.code_blobs:
            # Initialize a new code blob if the name is not already present
            self.code_blobs[name] = self.DEFAULT_OUTPUT.copy()
            
        for k, v in data.items():
            if k == CodeData.DEP:
                # Update dependencies by appending new dependencies to the existing list
                self.code_blobs[name][k] = self.code_blobs[name].get(k, []) + v
                for func in v:
                    # Recursively add each dependency with an empty dependency list
                    self.add(func, {CodeData.DEP: []})
            else:
                # Update other attributes
                self.code_blobs[name][k] = v
                 
    def dependancies(self, name):
        """
        Get the number of dependencies for a given code blob.
    
        Input:
            name (str): The name of the code blob to check for dependencies.
    
        Returns:
            int: The number of dependencies for the specified code blob.
    
        Raises:
            KeyError: If the specified code blob name doesn't exist in the code_blobs dictionary.
        """
        fobj = self.code_blobs.get(name, {})  # Retrieve the code blob object, default to an empty dictionary if not found
        return len(fobj.get(CodeData.DEP, []))  # Return the length of the dependencies list, default to empty list if not found
    
    def documented_dependancies(self, name):
        """
        Calculate the number of documented dependencies.
    
        Input:
        name (str): The name of the code blob to check for dependencies.
    
        Returns:
        int: The number of dependencies that are documented.
    
        Raises:
        KeyError: If accessing an attribute in `self.__getitem__(f)` fails.
    
        """
        fobj = self.code_blobs.get(name, {})  # Retrieve the code blob object by name, defaulting to an empty dict
        return len([f for f in fobj.get(CodeData.DEP, []) if self.__getitem__(f)[CodeData.DOC] != '-'])
        # Count dependencies where the documentation is present (not equal to '-')
            
    def undocumented_dependancies(self, name):
        """
        Calculate the number of undocumented dependencies for a given code blob.
    
        Input:
        - name: The name of the code blob to check for undocumented dependencies.
    
        Returns:
        - The number of undocumented dependencies for the given code blob.
    
        Raises:
        - KeyError: If the code blob name does not exist in self.code_blobs.
        """
        
        fobj = self.code_blobs.get(name, {})  # Retrieve the code blob object using the provided name
        # Count dependencies that do not have documentation
        return len(
            [f for f in fobj.get(CodeData.DEP, []) if not self.__getitem__(f)[CodeData.DOC] == '-']
        )

    def items(self):
        """
        Retrieve items from the code blobs.
    
        Input:
        None
    
        Returns:
        dict_items: An iterable view of the code blobs' items.
    
        Raises:
        AttributeError: If 'code_blobs' attribute does not exist in the class.
        """
        return self.code_blobs.items()

    def keys(self):
        """
        Retrieve the keys from the code_blobs attribute.
    
        Input:
        self: Reference to the current instance of the class.
    
        Returns:
        dict_keys: A view object that displays a list of all the keys in the code_blobs dictionary.
    
        Raises:
        AttributeError: If the code_blobs attribute does not exist.
        """
        return self.code_blobs.keys()

    def values(self):
        """
        Retrieve the values from the code_blobs dictionary.
    
        Input:
            None
    
        Returns:
            dict_values: An iterable view of the values in the code_blobs dictionary.
    
        Raises:
            AttributeError: If the 'code_blobs' attribute is not defined in the instance.
        """
        return self.code_blobs.values()
    
    def __str__(self):
        """
        Generates a summary string representation of the custom and reference functions.
    
        This function categorizes the functions stored in `self.code_blobs` into custom and reference functions.
        It then creates a formatted string detailing the custom functions along with their types, dependencies, and
        documented dependencies, followed by a list of reference functions.
    
        Input:
            self: Instance of the class containing the `code_blobs` attribute.
    
        Returns:
            str: A formatted string summarizing the custom and reference functions.
    
        Raises:
            None
        """
        
        # Separate custom and reference functions based on the `CodeData.CUSTOM` attribute
        custom_funcs = [(func, func_info) for func, func_info in self.code_blobs.items() if func_info[CodeData.CUSTOM]]
        ref_funcs = [(func, func_info) for func, func_info in self.code_blobs.items() if not func_info[CodeData.CUSTOM]]
        
        out_str = ''
        out_str += f'Custom ({len(custom_funcs)}):\n'  # Header for custom functions
        out_str += '-'*12 + '\n'
        
        # Add details of each custom function
        for func, func_info in custom_funcs:
            out_str += f'{func_info[CodeData.TYPE]:<10}: `{func}` Dependancies: {self.dependancies(func)}, Documented Dependancies: {self.documented_dependancies(func)}\n'
            
        out_str += f'\nReference ({len(ref_funcs)}):\n'  # Header for reference functions
        out_str += '-'*15 + '\n'
        
        # Add names of reference functions
        out_str += ', '.join([f'`{func}`' for func, _ in ref_funcs]) + '\n'
    
        return out_str

    def __repr__(self):
        """
        Provides a string representation of the object for debugging.
    
        Returns:
            str: A string representation of the object.
    
        This method uses the __str__ method to generate the string representation.
        """
        return self.__str__()


def clean_doc_str(doc_str):
    """
    Clean up the given documentation string by stripping leading and trailing whitespace and newline characters.
    
    Input:
    doc_str (str): The documentation string to be cleaned.
    
    Returns:
    str: The cleaned documentation string.
    
    Raises:
    None
    """
    doc_str = doc_str.strip()  # Remove leading and trailing whitespace
    doc_str = doc_str.lstrip('\n')  # Remove leading newline characters
    doc_str = doc_str.rstrip('\n')  # Remove trailing newline characters
    return doc_str
    
    
def get_reference_docs_simple_functions(import_stmts, funcs):
    """
    Fetch reference documentation for a list of functions after executing import statements.

    Input:
    - import_stmts: List of strings, where each string is an import statement to be executed.
    - funcs: List of strings, where each string is the full name of the function to fetch documentation for.

    Returns:
    - List of strings, where each string is the cleaned documentation string of the corresponding function in funcs. If no documentation is found, the string is '-'.

    Raises:
    - Any ImportError encountered during the execution of import statements is caught and logged using logging.debug.
    - Any Exception encountered during the evaluation of function documentation is silently ignored, and '-' is appended to the result list.
    """
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
            logging.debug(f'No reference documentation found for func: {func}')
    
    return docs


def get_reference_docs_custom_functions(func, code_dependancies):
    """
    Retrieves reference documentation for custom functions.

    Input:
    func: The target function for which reference documentation is needed.
    code_dependancies: A dictionary containing dependencies and their documentation details.

    Returns:
    A list of dictionaries, each containing 'function' and 'doc_str' keys for functions
    that have documentation.

    Raises:
    KeyError: If the specified function or its dependencies are not found in the provided dictionary.
    """
    
    ref_docs = []  # Initialize an empty list to hold reference documentation

    # Iterate over each dependency function for the given function
    for dep_func in code_dependancies[func][CodeData.DEP]:
        # Check if the dependency function has a short documentation string
        if code_dependancies[dep_func][CodeData.DOC_SHORT] != '-':
            # Append the dependency function and its documentation to the reference documentation list
            ref_docs.append({
                'function': dep_func,
                'doc_str': code_dependancies[dep_func][CodeData.DOC_SHORT]
            })

    return ref_docs  # Return the list of reference documentation


def get_summarized_docs(func_name, doc_str, mode, args):
    """
    Generate a summarized version of the documentation using an LLM.

    Input:
    - func_name (str): The name of the function for which the documentation is being summarized
    - doc_str (str): The original documentation string that needs to be summarized
    - mode (str): The mode in which the LLM should operate (e.g., "summarize")
    - args (dict): Additional arguments to be passed to the LLM

    Returns:
    - str: The summarized documentation generated by the LLM

    Raises:
    - ValueError: If any of the inputs are invalid or if the LLM returns an error
    """
    return get_llm_output(SYSTEM_PROMPT, DOC_SUMMARIZATION_PROMPT(func_name, doc_str), mode, args)


def get_truncated_docs(func_name, doc_str):
    """
    Truncate the documentation string to the first paragraph or line.

    Input:
    func_name (str): The name of the function whose documentation is being truncated.
    doc_str (str): The full documentation string to be truncated.

    Returns:
    str: The truncated documentation string.

    Raises:
    None
    """
    # Split the doc string by double newlines and take the first part
    trunc_doc_str = doc_str.split('\n\n')[0]  
    if len(trunc_doc_str) == len(doc_str):  
        # If no double newline was found, split by a single newline
        trunc_doc_str = doc_str.split('\n')[0]
        
    # Log the truncation details
    logging.debug(f'Truncated doc for {func_name} from {len(doc_str)} to {len(trunc_doc_str)}')
        
    return trunc_doc_str


def get_shortened_docs(func_name, doc_str, mode, llm_mode, args):
    """
    Get a shortened version of the documentation based on the specified mode.

    Inputs:
    - func_name: The name of the function whose documentation is being shortened.
    - doc_str: The original documentation string.
    - mode: The mode to use for shortening the documentation. Can be 'summarize', 'truncate', or 'full'.
    - llm_mode: The mode for the language model, used when mode is 'summarize'.
    - args: Additional arguments required for the summarization process.

    Returns:
    - A shortened version of the documentation string based on the specified mode.

    Raises:
    - None. Logs a warning if an unknown mode is specified and defaults to truncation.
    """
    if not doc_str or doc_str == '-':
        # Return the original if it's empty or just a dash
        return doc_str

    if mode == 'summarize':
        return get_summarized_docs(func_name, doc_str, llm_mode, args)
    elif mode == 'truncate':
        return get_truncated_docs(func_name, doc_str)
    elif mode == 'full':
        return doc_str
    else:
        # Log a warning if an unknown mode is specified and default to truncation
        logging.warning(f'Could not shorten doc for `{func_name}` using mode: `{mode}`, using truncation')
        return get_truncated_docs(func_name, doc_str)