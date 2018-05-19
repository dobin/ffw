#!/bin/bash

# via https://stackoverflow.com/questions/3925075/how-to-extract-only-the-raw-contents-of-an-elf-section

IN_F=$1
OUT_F=./tmp1.bin
SECTION=.rodata

objdump -h $IN_F |
  grep $SECTION |
    awk '{print "dd if='$IN_F' of='$OUT_F' bs=1 count=$[0x" $3 "] skip=$[0x" $6 "]"}' |
      bash


SECTION=.data
OUT_F=./tmp2.bin
objdump -h $IN_F |
  grep $SECTION |
    awk '{print "dd if='$IN_F' of='$OUT_F' bs=1 count=$[0x" $3 "] skip=$[0x" $6 "]"}' |
      bash

strings ./tmp1.bin > dict
strings ./tmp2.bin >> dict

cat dict | egrep -v '\%|\*|\-\-|\.c|\(\)' | sed '/^.\{16\}./d' > dict2

sort -u dict2 > dictionary.txt

rm tmp1.bin tmp2.bin dict dict2
