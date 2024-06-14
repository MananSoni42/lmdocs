# lmdocs: Generative AI for code documentation :brain: :arrow_right: :computer: :snake:

lmdocs is a Python tool that automatically generates documentation for your code using LLMs.

## Features
* **Codebase Preservation**: _Guarantees_ no changes to your code, only adds helpful comments
* **Automatic Documentation Extraction**: Extracts and references documentation from imported libraries
* **LLM-Generated Comments**: Utilizes your favourite LLM to generate readable comments, ensuring your code is well-documented

## lmdocs in Action :hammer:
<table>
<tr>
<th> Before </th>
<th> After </th>
</tr>
<tr>
<td>

```python
def fibonacci(n):
    a, b = 0, 1
    fib_seq = []
    for i in range(n):
        fib_seq.append(a)
        a, b = b, a + b
    return fib_seq
```

</td>
<td>

```python
def fibonacci(n):
    """
    Generates the Fibonacci sequence up to n terms.
    
    Input:
        n (int): The number of terms in the Fibonacci sequence to generate.
        
    Returns:
        list: A list containing the first n terms of the Fibonacci sequence.
        
    Raises:
        ValueError: If n is less than 1.
    """
    
    a, b = 0, 1 # Initialize two variables to store the last and current term in the sequence
    fib_seq = [] # Initialize an empty list to store the generated Fibonacci sequence
    
    for i in range(n): # Generate n terms of the Fibonacci sequence
        fib_seq.append(a) # Append the current term to the sequence
        
        # Update the last two terms for the next iteration
        a, b = b, a + b 
    
    return fib_seq # Return the generated Fibonacci sequence
```

</td>
</tr>
</table>

The example above was generated using the [DeepSeek coder 6.7B](https://huggingface.co/TheBloke/deepseek-coder-6.7B-instruct-GGUF) model.

## Quickstart :rocket:
### Using an OpenAI model
```bash
python lmdocs.py <project path> --openai_key <key> 
```

Tested with `gpt-3.5-turbo`, `gpt-4-turbo`, `gpt-4o`

### Using a local model
```bash
python lmdocs.py <project path> --port <local LLM server port>
```

#### Setup
To use local LLMs, you need to set up an openAI compatible server.  
You can use local desktops apps like [LM Studio](https://lmstudio.ai/docs/local-server), [Ollama](https://ollama.com/blog/openai-compatibility), [GPT4All](https://docs.gpt4all.io/gpt4all_chat.html#server-mode), [llama.cpp](https://github.com/ggerganov/llama.cpp/tree/master/examples/server) or any other method to set up your LLM server.

Although lmdocs is compatible with any local LLM, I have tested that it works for the following models:  
[`deepseek-coder-6.7b-instruct`](https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-instruct), [`WizardCoder-Python-7B-V1`](https://huggingface.co/TheBloke/WizardCoder-Python-7B-V1.0-GGUF), [`Meta-Llama-3-8B-Instruct`](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct), [`Mistral-7B-Instruct-v0.2`](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2), [`Phi-3-mini-4k-instruct`](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct)

### Additional options :gear:
```bash
usage: lmdocs.py [-h] [-v] [--openai_key OPENAI_KEY] [--openai_key_env OPENAI_KEY_ENV] [--openai_model {gpt-3.5-turbo,gpt-4-turbo,gpt-4o}] [-p PORT]
                 [--max_retries MAX_RETRIES] [--ref_doc {truncate,summarize,full}]
                 path

positional arguments:
  path                  Path to the file/folder of project

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Give out verbose logs
  --openai_key OPENAI_KEY
                        Your Open AI key
  --openai_key_env OPENAI_KEY_ENV
                        Environment variable where Open AI key is stored
  --openai_model {gpt-3.5-turbo,gpt-4-turbo,gpt-4o}
                        Which openAI model to use. Supported models are ['gpt-3.5-turbo', 'gpt-4-turbo', 'gpt-4o']            
                        gpt-3.5-turbo is used by default
  -p PORT, --port PORT  Port where Local LLM server is hosted
  --max_retries MAX_RETRIES
                        Number of attempts that the LLM gets to generate the documentation for each function
  --ref_doc {truncate,summarize,full}
                        Strategy to process reference documentation. Supported choices are:            
                        truncate    - Truncate documentation to the first paragraph            
                        summarize   - Generate a single summary of the documentation using the given LLM            
                        full        - Use the complete documentation (Can lead to very long context length)            
                        "truncate" is used as the default strategy
```

## Caveats and known limitations

### Language Support
Currently supports only Python (3.8+)

### Dependancy extraction
The `ast` module is used to analyze the Abstract Syntax Tree of every Python file in the codebase.  
Only functional and class dependancies are tracked i.e Only code written in a class or function, is tracked and documented

### Package Dependancies
lmdocs is written in pure Python, it does not depend on any other packages.  
It is strongly recommended that you install the libraries/packages for the project that needs to be documented for reference document extraction

### Reference documentation extraction

Documentation for functions which have no dependancies is not extracted from their docstring using Pythons `___doc___()` method
For external libraries (e.g numpy), the library is imported as it is from the original code

## TODO

- [ ] Add reason for AST not matching
- [ ] Add support for lambdas

## Contributing
Contributions from the community are welcome. Feel free to submit feature requests and bug fixes by opening a new issue.  
Together, we can make lmdocs even better!

## License 
lmdocs is released under the [GNU AGPL v3.0](https://www.gnu.org/licenses/agpl-3.0.en.html) License  
For personal or open-source projects, you are free to use, modify, and distribute lmdocs under the terms of the AGPLv3 license.  
If you plan to incorporate lmdocs into a proprietary application or service, you are required to provide access to the complete source code of your application, including any modifications made to lmdocs.
