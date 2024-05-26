# Gendocs: Generative AI for code documentation :brain: :arrow_right: :computer:
Generates documentation for your code using your favourite state-of-the art LLMs!

## Features
[x] Extracts and references documentation from your imported libraries
[ ] _Guarantees_ no changes to the original codebase, Only adds comments
[x] Works with local models as well as OpenAI models

## Usage
```
python gendocs <project_folder> 
```

### Using an OpenAI model
1. TODO

### Using a local model
1. Start your local LLM with an openAI compatible server on any port, say 1234 (Local LLM servers: [LM Studio](https://lmstudio.ai/docs/local-server), [Ollama](https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-chat-completion))

### Additional options
Refer `python gendocs --help` for more options


## Caveats and known limitations

### Dependancy extraction
The `ast` module is used to analyze the Abstract Syntax Tree of every *Python* file in the codebase. 
Only functional and class dependancies are tracked i.e If the code is not written in a class or function, it is not tracked and documented

### Known documentation extraction

Functions which have no dependancies are called simple functions

Documentation for these functions are extracted from their  docstring using Pythons `___doc___()` method

#### Example 1: 
Function: `range`

#### Example 2:
Function `np.arange`

#### Example 3:
Code: 
```python
a,b = {1,2,3}, {3,4,5}
a.intersection(b)
```
Not able to extract

## License
GPL v3

