# Prem

Pipe remedy: CLI-like utils in Python.

```py
# before
import pathlib, re
"".join(
    line.replace("h", "H")
    for filename in pathlib.Path().glob("*.md")
    for line in filename.read_text().splitlines(keepends=True)
    if re.search("hello", line)
)

# after
from prem import ls, xargs, cat, grep, sed
str(ls("*.md") | xargs(cat) | grep("hello") | sed("s/h/H/g"))
```
