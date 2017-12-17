# Fuzzing Problems FAQ

## "Could not connect" / "Socket Error"

Note: If your project is unable to specify a target port
on the command line, adjust `baseport` to the hardcoded port
in the software project, and set `processes=1`:

```
    "target_args": "", # no port specification possible
    "baseport": 8080,  # set this to the target's port
    "processes": 1,    # can only set one process
```

But: It is preferable to just patch the source code of the target
so it takes the listening port from the command line.


## No new basic blocks on feedback driven fuzzing

Make sure you compile the target with the correct flags,
or the correct honggfuzz based compiler. Also set the hfuzz flags:

Set arguments manually:
```
export CFLAGS="-fsanitize-coverage=trace-pc-guard,indirect-calls,trace-cmp -fsanitizer=address"
```

Or:

Clang:
```
    export HFUZZ_CC_ASAN="true"
    export CC=/opt/honggfuzz/hfuzz_cc/hfuzz-clang
    export CXX=/opt/honggfuzz/hfuzz_cc/hfuzz-clang++
```

GCC:
```
    export HFUZZ_CC_ASAN="true"
    export CC=/opt/honggfuzz/hfuzz_cc/hfuzz-gcc
    export CXX=/opt/honggfuzz/hfuzz_cc/hfuzz-g++
```


# Compiling

## Sanitizer=address linker error

If you get something like this upon compiling:
```
undefined reference to __asan_report_store8
```

Do:
```
export LDFLAGS="-fsanitize=address"
```

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
