

# Various infos

## Notes on (obsolete) python-ptrace

python-ptrace does not yield good results, and is currently disabled.

If you want to use `python-ptrace` in verifier mode, install it:
```
pip install python-ptrace
```

And fix it.

### Fix ptrace

python-ptrace sometimes encounters a bug. Fix the regex specified below.
The path may be different (depending on how you installed pytohn-ptrace).
May not be always necessary (?). Will only affect verify-mode of ffw.

* Relevant file: memory_mapping.py
* Relevant part: PROC_MAP_REGEX

/usr/local/lib/python2.7/dist-packages/ptrace/debugger/memory_mapping.py
```
PROC_MAP_REGEX = re.compile(
    r'([0-9a-f]+)-([0-9a-f]+) '
    r'(.{4}) '
    r'([0-9a-f]+) '
    r'([0-9a-f]+):([0-9a-f]+) ' # replace orig line with this one
    r'([0-9]+)'
    r'(?: +(.*))?'
)
```


## Config

If in doubt:

```
sysctl net.core.somaxconn=4096
ulimit -c 999999
```

Or run as root.

## Compile targets

Use the following compile flags to increase bug detection rate
(with ASAN) and backtrace quality:
```
export CFLAGS="-fsanitize=address -fno-omit-frame-pointer"
```
