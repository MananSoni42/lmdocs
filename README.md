# lmdocs: Generative AI for code documentation :brain: :arrow_right: :computer: :snake:
`lmdocs` automatically generates documentation for your Python code using LLMs.

( [Features](#features) | [Examples](#lmdocs-in-action-hammer) | [Quickstart :rocket:](#quickstart-rocket) | [How it works](#how-it-works) | [Additional options :gear:](#additional-options-gear) | [Caveats and limitations](#caveats-and-limitations) )

## Features
* **Codebase Preservation**: _Guarantees_ no changes to your code, only adds helpful comments
* **Automatic Documentation Extraction**: Extracts and references documentation from imported libraries
* **LLM-Generated Comments**: Understands your code and adds a relevant docstring and inline comments
* **No dependancies**: Written in pure Python, no dependancies on any external packages
 *It is recommended that you install libraries specific to your project before running

## lmdocs in Action :hammer:

```python
# Original function
def fibonacci(n):
    a, b = 0, 1
    fib_seq = []
    for i in range(n):
        fib_seq.append(a)
        a, b = b, a + b
    return fib_seq

# Commented using lmdocs
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

```python
# Original function
def k_means(X, k, max_iter=300, tol=1e-4, random_state=None):
    np.random.seed(random_state)
    centroids = X[np.random.choice(X.shape[0], k, replace=False), :]
    
    for _ in range(max_iter):
        distances = np.sqrt(((X - centroids[:, np.newaxis])**2).sum(axis=2)) 
        cluster_assignments = np.argmin(distances, axis=0)
        new_centroids = np.array([X[cluster_assignments == i].mean(axis=0) for i in range(k)])  
        
        if np.abs(centroids - new_centroids).sum() < tol:
            break
            
        centroids = new_centroids
        
    return cluster_assignments, centroids

# Commented using lmdocs
def k_means(X, k, max_iter=300, tol=1e-4, random_state=None):
    '''
    Perform K-Means clustering. 
    
    Input: 
        X : array-like of shape (n_samples, n_features)
            The input data.
        
        k : int
            The number of clusters to form.
            
        max_iter : int, default=300
            Maximum number of iterations of the k-means algorithm for a single run.
                
        tol : float, default=1e-4
            Relative tolerance with regards to Frobenius norm of the difference in the cluster centers 
            of two consecutive iterations to declare convergence.
            
        random_state : int, default=None
            Determines random number generation for centroid initialization. Use an integer to 
            get reproducible results.
    
    Returns: 
        tuple : (cluster_assignments, centroids)
        
            cluster_assignments : array-like of shape (n_samples,)
                Cluster assignments for each sample in the input data.
                
            centroids : array-like of shape (k, n_features)
                Coordinates of cluster centers.
    
    Raises: 
        ValueError : If k greater than number of samples or less than one.
        
    '''
    np.random.seed(random_state)
    centroids = X[np.random.choice(X.shape[0], k, replace=False), :]
    
    for _ in range(max_iter):
        distances = np.sqrt(((X - centroids[:, np.newaxis])**2).sum(axis=2))  # Calculate Euclidean distance to each centroid
        cluster_assignments = np.argmin(distances, axis=0)  # Assign sample to nearest centroid
        
        # Recalculate centroids as mean of samples in the same cluster
        new_centroids = np.array([X[cluster_assignments == i].mean(axis=0) for i in range(k)])  
        
        if np.abs(centroids - new_centroids).sum() < tol:  # Check if centroids have converged
            break
            
        centroids = new_centroids  # Update centroids for next iteration
    
    return cluster_assignments, centroids
```

The examples above were generated locally using lmdocs with the [DeepSeek coder 6.7B](https://huggingface.co/TheBloke/deepseek-coder-6.7B-instruct-GGUF) model.

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

## How it works
**Step 1: Collect and Analyze Code**  
Gather all Python files from the project directory and identify all function, class, and method calls

**Step 2: Create Dependency Graph**  
Map out the dependencies between the identified calls to create a dependency graph of the entire codebase

**Step 3: Retrieve and Generate Documentation**  
For calls with no dependencies, retrieve existing documentation using their `__doc__` attribute  
For calls with dependents, prompt the LLM to generate documented code, providing the original code and reference documentation for its dependencies in the prompt  

**Step 4: Verify and Replace Code**  
Compare the Abstract Syntax Tree (AST) of the original and generated code  
If they match, replace the original code with the documented code  
If they don't match, retry the generation and verification process (up to three times)  

### Additional options :gear:
```bash
usage: lmdocs.py [-h] [-v] [--openai_key OPENAI_KEY] [--openai_key_env OPENAI_KEY_ENV] [--openai_model {gpt-3.5-turbo,gpt-4-turbo,gpt-4o}] [-p PORT]
                 [--ref_doc {truncate,summarize,full}] [--max_retries MAX_RETRIES] [--temperature TEMPERATURE] [--max_tokens MAX_TOKENS]
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
  --ref_doc {truncate,summarize,full}
                        Strategy to process reference documentation. Supported choices are:            
                        truncate    - Truncate documentation to the first paragraph            
                        summarize   - Generate a single summary of the documentation using the given LLM            
                        full        - Use the complete documentation (Can lead to very long context length)            
                        "truncate" is used as the default strategy
  --max_retries MAX_RETRIES
                        Number of attempts that the LLM gets to generate the documentation for each function/method/class
  --temperature TEMPERATURE
                        Temperature parameter used to sample output from the LLM
  --max_tokens MAX_TOKENS
                        Maximum number of tokens that the LLM is allowed to generate
```

## Caveats and limitations

### Language Support  
Only supports Python 3.0+

### Dependancy extraction  
The `ast` module is used to analyze the Abstract Syntax Tree of every Python file in the codebase.  
Only functional and class dependancies are tracked i.e Only code written within a class, method or function, is tracked and documented

### Package Dependancies  
lmdocs is written in pure Python, it does not depend on any other packages.  
It is strongly recommended that you install the libraries/packages for the project that needs to be documented for reference document extraction

### Reference documentation extraction  
Documentation for functions which have no dependancies is extracted using Pythons `___doc___()` method  
For external libraries (e.g numpy), the library is imported as it is from the original code  

Note that, since Python does not have have static types, not all documentation can be extracted correctly.
```python
# Original code
a = {1,2,3,4,5}
b = a.intersection({2,4,6})

# Documentation extraction for intersection
doc_str = a.intersection.__doc__() # Fails
doc_str = intersection.__doc__() # Fails
# Need to know the type of a which is only available at runtime.
# Successfull call will look like: set.intersection.__doc__()
```

## Contributing
Contributions from the community are welcome. Feel free to submit feature requests and bug fixes by opening a new issue.  
Together, we can make lmdocs even better!

## License 
lmdocs is released under the [GNU AGPL v3.0](https://www.gnu.org/licenses/agpl-3.0.en.html) License  
For personal or open-source projects, you are free to use, modify, and distribute lmdocs under the terms of the AGPLv3 license.  
If you plan to incorporate lmdocs into a proprietary application or service, you are required to provide access to the complete source code of your application, including any modifications made.
