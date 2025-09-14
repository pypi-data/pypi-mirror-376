import re
import warnings
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

# version detector. Precedence: installed dist, git, 'UNKNOWN'
try:
    from ._dist_ver import __version__
except ImportError:
    try:
        from setuptools_scm import get_version

        __version__ = get_version(root="../..", relative_to=__file__)
    except (ImportError, LookupError):
        __version__ = "UNKNOWN"


class Pipe(ABC):
    @abstractmethod
    def __iter__(self):
        ...

    def __str__(self):
        return "\n".join(map(str, self)) + "\n"

    def __or__(self, other):
        other.input = self
        return other

    def __lt__(self, other):
        self.input = other
        return self

    def __lshift__(self, other):
        return self < other


class ls(Pipe):
    def __init__(self, path="*"):
        self.path = path

    def __iter__(self):
        if self.path[0] in "/\\":             # linux absolute
            yield from Path(self.path[0]).glob(self.path[1:])
        elif self.path[1:3] in {':/', ':\\'}: # windows
            yield from Path(self.path[:3]).glob(self.path[3:])
        else:                                 # relative
            yield from Path().glob(self.path)


class xargs(Pipe):
    """xargs -n1"""
    def __init__(self, cmd: Pipe):
        self.cmd = cmd

    def __iter__(self):
        it = self.input.splitlines() if isinstance(self.input, str) else self.input
        for line in it:
            yield from self.cmd(line)


class cat(Pipe):
    def __init__(self, filename, *, encoding: Optional[str] = None):
        self.filename = filename
        self.encoding = encoding

    def __str__(self):
        return Path(self.filename).read_text(encoding=self.encoding)

    def __iter__(self):
        with Path(self.filename).open(encoding=self.encoding) as fd:
            yield from fd


class grep(Pipe):
    """grep -E"""
    def __init__(self, pattern: str, *, only_matching: Optional[bool] = None, ignore_case: bool = False,
                 dot_all: bool = False, invert_match: bool = False):
        flags = re.M
        if ignore_case:
            flags |= re.I
        if dot_all:
            flags |= re.S
            if only_matching is None:
                only_matching = True
            if not only_matching:
                warnings.warn("Likely incompatible: `dot_all and not only_matching`", UserWarning, stacklevel=2)
        if invert_match:
            if only_matching is None:
                only_matching = True
            if not only_matching:
                warnings.warn("Likely incompatible: `invert_match and not only_matching`", UserWarning, stacklevel=2)
        self.regex = re.compile(pattern if only_matching else f".*{pattern}.*", flags=flags)
        self.invert_match = invert_match

    def __iter__(self):
        if isinstance(self.input, str):
            if self.invert_match:
                yield from (line for line in self.input.splitlines() if not self.regex.search(line))
            else:
                yield from (i.group() for i in self.regex.finditer(self.input))
        else:
            if self.invert_match:
                yield from (line for line in iter(self.input) if not self.regex.search(str(line)))
            else:
                for line in iter(self.input):
                    yield from (i.group() for i in self.regex.finditer(line))


class sed(grep):
    """sed -r"""
    def __init__(self, expression: str, *, quiet: bool = False):
        match = re.match(
            "(?P<cmd>[sy]?)(?P<delim>.)(?P<pattern>.*?)(?P=delim)(?P<repl>.*?)(?P=delim)?(?P<options>[gpdi]*?)$",
            expression)

        m = match.groupdict() # type: ignore[union-attr]

        options = set(m['options'])
        if m['cmd'] == 's':
            if 'd' in options:
                raise ValueError("`s/.../.../d` not allowed")
        elif m['cmd'] == 'y':
            raise NotImplementedError('`y/.../.../`')
        else:
            if m['repl']:
                raise ValueError("`/.../.../` not allowed. Did you forget to prefix `s`?")
            if 'd' in options:
                if 'p' in options:
                    raise ValueError("`/.../dp` not allowed")
                if 'g' in options:
                    raise ValueError("`/.../dg` not allowed")
                if quiet:
                    raise ValueError("`/.../d` and `quiet` not allowed")
        super().__init__(m['pattern'], only_matching=m['cmd'] == 's' or 'd' in options, ignore_case='i' in options,
                         invert_match='d' in options)
        self.cmd = m['cmd']
        self.repl = m['repl']
        self.options = options
        self.quiet = quiet

    def __iter__(self):
        if 'd' in self.options:
            yield from super().__iter__()
            return
        elif self.cmd != 's':
            raise ValueError("unknown")

        if self.quiet:
            raise NotImplementedError("quiet")
        if 'p' in self.options:
            raise NotImplementedError("`/.../p`")

        if isinstance(self.input, str):
            if 'g' in self.options:
                yield from self.regex.sub(self.repl, self.input).splitlines()
            else:
                yield from (self.regex.sub(self.repl, line, count=1) for line in self.input.splitlines())
        else:
            yield from (self.regex.sub(self.repl, line, count=0 if 'g' in self.options else 1)
                        for line in iter(self.input))
