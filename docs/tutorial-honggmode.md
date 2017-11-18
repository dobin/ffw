
## Honggmode

Honggmode uses hongfuzz for feedback driven fuzzing. It requires an up to date kernel and clang version. Tested on Ubuntu 17.04.

### Setup honggfuzz

Use the ffw-honggfuzz repository, and compile it:
```
git clone https://github.com/dobin/honggfuzz
make
make install
```

Specify location of honggfuzz in `fuzzing.py`:
```
"honggpath": "/home/fuzzer/honggfuzz/honggfuzz",
```

### Setup an open-source project

Compile target with:
```
export HFUZZ_CC_ASAN="true"
export CC=~/honggfuzz/hfuzz_cc/hfuzz-clang
```

### Setup a closed-source project

Add one of the following options. See https://github.com/google/honggfuzz/blob/master/docs/FeedbackDrivenFuzzing.md for reference. `--linux_perf_bts_edge` works well.

```
"honggmode_option": "--linux_perf_bts_edge"
"honggmode_option": "--linux_perf_ipt_block"
"honggmode_option": "--linux_perf_instr"
"honggmode_option": "--linux_perf_branch"
```

### Fuzz

Start with:
```
./fuzzing.py honggmode
```
Instead of `./fuzzing.py fuzz`
