# lmdocs: Generative AI for code documentation :brain: :arrow_right: :computer:
Generates documentation for your code using your favourite state-of-the art LLMs!

lmdocs is a tool that generates documentation for your code using state-of-the-art LLMs. It can: 
* Extract and reference documentation from imported libraries
* Ensures that your codebase remains unchanged while adding helpful comments

## Usage
### Using an OpenAI model
```bash
python lmdocs.py <project path> --openai_key <key> 
```

#### Tested models
`gpt-3.5-turbo`, `gpt-4-turbo`, `gpt-4o`

### Using a local model
```bash
python lmdocs.py <project path> --port <local LLM server port>
```

#### Setup
Start your local LLM with an openAI compatible server on any port, say 1234 (Local LLM servers: [LM Studio](https://lmstudio.ai/docs/local-server), [Ollama](https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-chat-completion))

#### Tested models
Although lmdocs is compatible with any local LLM, I have personally tested that it works for the following models: 
`deepseek coder 7B`, `wizard coder v1 7B`, `llama3 7B instruct`, `mistral 7B instruct v0.1`, `mistral 7B instruct v0.2`, `mistral 7B instruct v0.3`, `phi3 mini`

### Additional options
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
                        Which openAI model to use. Supported models are [gpt-3.5-turbo, gpt-4-turbo, gpt-4o]. gpt-3.5-turbo is used by default
  -p PORT, --port PORT  Port where Local LLM server is hosted
  --max_retries MAX_RETRIES
                        Number of attempts to give the LLM to generate the documentation for each function
  --ref_doc {truncate,summarize,full}
                        How to process reference documentation. Supported choices are: [truncate / summarize / full]
```

## Caveats and known limitations

### Language Support
Currently supports only Python (3.8+)

### Code extraction
The `ast` module is used to analyze the Abstract Syntax Tree of every Python file in the codebase. 
Only functional and class dependancies are tracked i.e If the code is not written in a class or function, it is not tracked and documented

### Dependancies
lmdocs does not depend on any other packages.
It is strongly recommended that you install the libraries/packages for the project that needs to be documented as these are needed for reference document extraction

### Reference documentation extraction

Documentation for Functions which have no dependancies are extracted from their docstring using Pythons `___doc___()` method
For external libraries (e.g numpy), the library is imported as it is from the original code

#### Example 1:
Original Code:
```
a = []
for i in range(5):
    a.append(i**2)
```

Document Extraction code:
```python
doc_str = range.__doc__() # Success
```

#### Example 2: 
Original Code:
```python
import numpy as np
x = np.linspace(0,10,5)
```

Document Extraction code:
```python
import numpy as np
doc_str = np.linspace.__doc__() # Success
``` 

#### Example 2: 
Original Code:
```python
import numpy as np
x = np.linspace(0,10,5)
```

Document Extraction code:
```python
import numpy as np
doc_str = np.linspace.__doc__() # Success
```

#### Example 3: 
Original Code:
```python
a = {1,2,3,4,5}
b = a.intersection({2,4,6})
```

Document Extraction code:
```python
doc_str = a.intersection.__doc__() # Fails
doc_str = intersection.__doc__() # Fails
# Need to know the type of a which is only available at runtime.
# Successfull call will look like: set.intersection.__doc__()
```

## TODO

- [x] Handle imports in generated code
- [x] Change nodes in file
- [x] Add support for openAI models
- [x] Test more common open source models
- [x] Improve readme - No deps, Better explanations
- [ ] Improve logging + add verbose argument and logging.debug calls
- [ ] Refactor code (main.py)
- [ ] Add argument for ony docstring generation
- [x] Improve code indent detection algo
- [ ] Add support for lambdas
- [ ] Add support/test for functions with existing docs
- [ ] Add example of documented function in readme

## License 
[GNU AGPL v3.0](https://www.gnu.org/licenses/agpl-3.0.en.html)