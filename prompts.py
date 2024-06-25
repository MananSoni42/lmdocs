def format_docs(ref_docs):
    return '\n\n'.join(f'Function: {ref_doc["function"]}\nDocumentation: {ref_doc["doc_str"]}' for ref_doc in ref_docs)


SYSTEM_PROMPT = 'You are an intelligent AI programming assistant. You are fluent in Python and only answer questions related to Computer Science'

INSTRUCTIONS = '''\
- Generate documentation for the python function/class given below.
- The documentation should contain:
- Docstring
    - Should be declared using “”” triple double quotes “”” just below the original class, method, or function definition.
    - Should contain:
        - A single line summary 
        - Input: Short descriptions of each input parameter
        - Returns: Short descriptions of each output parameter
        - Raises: Short description of failure cases and exceptions raised by the class, method, or function
- Inline comments
    - Short inline comments for blocks of code that are hard to understand
    - Only write such comments for each block of code, not for every line
- You also have access to reference documentation for sub-functions and sub-classes used in the original class, method, or function. These should be used for enhanced context for better documentation.
- Preserve all existing documentation given in the original class, method, or function.
- Do not change the code, name or existing comments of the original class, method, or function, only add comments wherever necessary.
- Do not add any import statements
- Only reply with the documented class, method, or function within ``` tags followed by the stop token: <STOP>'''


DOC_GENERATION_PROMPT = lambda func, ref_docs: f'''\
### Guidelines:
{INSTRUCTIONS}

### Reference documentation:
{format_docs(ref_docs)}

### Original code block:
```python
{func}
```

### Original code block with documentation:
```python
'''


DOC_SUMMARIZATION_PROMPT = lambda func, doc: f'''\
### Guidelines
Summarize the given function documentation in a single line.
Make sure that the key nuances and overall meaning of the documentation are captured in the summary
Ony Reply with only the summarized documentation followed by the stop token <STOP>

### Original documentation
Function: {func}
{doc}

### Summarized documentation
'''