from pathlib import PathInstall
```bash
pip install secret_generator
```

Example:

1) 
```python
from secret_generator import generate_secret

print(generate_secret(40))
``` 
ore
```python
from secret_generator import run_generate_secret

run_generate_secret()
```
2) 
```python
from pathlib import Path
from os import getcwd

from secret_generator import generate_htpasswd


print(generate_htpasswd("username", "password", Path(getcwd()) / ".htpasswd"))
``` 
ore
```python
from secret_generator import run_generate_htpasswd

run_generate_htpasswd()
```
