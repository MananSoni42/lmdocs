# Gendocs: Generative AI for code documentation :brain: :arrow_right: :computer:
Generates documentation for your code using your favourite state-of-the art LLMs!

Gendocs is a tool that generates documentation for your code using state-of-the-art LLMs. It can: 
* extract and reference documentation from imported libraries
* Ensures that your codebase remains unchanged while adding helpful comments.

## Usage
```
python gendocs <project_folder> 
```

### Using an OpenAI model
#### Setup
TODO

#### Tested models
TODO

### Using a local model
#### Setup
Start your local LLM with an openAI compatible server on any port, say 1234 (Local LLM servers: [LM Studio](https://lmstudio.ai/docs/local-server), [Ollama](https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-chat-completion))

#### Tested models
Tested with `deepseek coder`

### Additional options
Refer `python gendocs --help` for more options


## Caveats and known limitations

### Language Support
Currently supports only Python (3.8+)

### Dependancy extraction
The `ast` module is used to analyze the Abstract Syntax Tree of every Python file in the codebase. 
Only functional and class dependancies are tracked i.e If the code is not written in a class or function, it is not tracked and documented

### Known documentation extraction

Functions which have no dependancies are called simple functions
Documentation for these functions are extracted from their docstring using Pythons `___doc___()` method
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
- [ ] Add support for openAI models
- [ ] Test more common open source models
- [ ] Improve readme - No deps, Better explanations
- [ ] Improve logging + add verbose argument and logging.debug calls
- [ ] Refactor code (main.py)
- [ ] Add argument for ony docstring generation
- [x] Improve code indent detection algo
- [ ] Add support for lambdas

## License 
[GNU AGPL v3.0](https://www.gnu.org/licenses/agpl-3.0.en.html)
