def format_docs(ref_docs):
    return '\n\n'.join(f'Function: {ref_doc["function"]}\nDocumentation: {ref_doc["doc_str"]}' for ref_doc in ref_docs)


SYSTEM_PROMPT = 'You are an intellighent AI programming assistant. You are fluent in Python and only answer questions related to Computer Science'


INSTRUCTIONS = '''\
- Generate documentation for the python function given below.
- The documentation should contain:
- Docstring
    - A docstring with a single line description summarizing the function
    - Short descriptions of each input parameter
    - Short descriptions of each output parameter
- Inline comments
    - Short inline comments for blocks of code that are hard to understand
    - Only include where the code functionality is not obvious
- You also have access to reference documentation for sub-functions and sub-classes used in the primary function. These should be used for enhanced context for better documentation of the original function.
- Preserve all existing documentation of the original function.
- Do not change the original function, only add comments wherever necessary.
- Use the same variables and logic, only add comments
- Only reply with the documented function within ``` tags.'''


FUNCTION_DOC_GENERATION_PROMPT = lambda func, ref_docs: f'''\
### Guidelines
{INSTRUCTIONS}

### Original function 
```python
{func}
```

### Reference documentation
{format_docs(ref_docs)}

### Original function with documentation
```python
'''


SUMMARIZE_DOC_PROMPT = lambda func, doc: f'''\
### Guidelines
Summarize the given function documentation in a single line.
Make sure that the key nuances and overall meaning of the documentation are captured in the summary
Ony Reply with only the summarized documentation followed by <STOP>

### Original documentation
Function: {func}
{doc}

### Summarized documentation
'''