#!/usr/bin/python
#
# A dumb fuzzer employing several different fuzzing techniques
#

import sys
import os
import random
import struct

# Amount of file to mutate
MIN_CORRUPT = 0.0005
MAX_CORRUPT = 0.003

CHUNKSIZE = 1024

def byteFlip(inFile):
    """
    Flip all bits in the byte
    """
    return chr(ord(inFile.read(1)) ^ 0xFF)

def bitFlip(inFile):
    """
    Flip a random bit in the byte
    """
    bit = 1 << random.randrange(0, 8)
    return chr(ord(inFile.read(1)) ^ bit)

def randomReplace(inFile):
    """
    Replace a byte with a random byte
    """
    inFile.seek(1, 1)
    return chr(random.randrange(0, 256))

def arithmetic(inFile):
    """
    Perform arithmetic on varying sized values
    """
    length, pattern, value_max = random.choice([(1,"<b", 0x7f),(2,"<h", 0x7fff),
        (4,"<l", 0x7fffffff)])
    tmp = inFile.read(length)
    if len(tmp) < length:
        return tmp

    value = struct.unpack(pattern, tmp)[0]

    # Slide the value
    value += random.randrange(-5, 6)

    value_min = -1 * (value_max + 1)
    if value > value_max:
        value = (value & value_max) + value_min
    elif value < value_min:
        value = (value & value_max) * -1

    return struct.pack(pattern, value)

def replaceConstant(inFile):
    """
    Replace some bytes with an 'interesting' constant
    """
    raise NotImplementedError()

MUTATORS = [
    byteFlip,
    bitFlip,
    randomReplace,
    arithmetic,
    #replaceConstant,
]

def copyData(inFile, outFile, count):
    """
    Copy count bytes from the input file to the output file
    """
    current = 0
    while current < count:
        readSize = min(CHUNKSIZE, count-current)
        data = inFile.read(readSize)
        outFile.write(data)
        current += readSize

def usage():
    print "%s: <seed> <input file> <output file>" % (sys.argv[0])
    sys.exit(-1)

def main():
    if len(sys.argv) < 4:
        usage()

    # Seed the random number generator
    random.seed(int(sys.argv[1]))

    # Get the size of the input file
    size = os.path.getsize(sys.argv[2])

    # Generate a bunch of offsets for data we are going to corrupt and sort them
    offsets = []
    corrupt_pct = (random.random() * (MAX_CORRUPT - MIN_CORRUPT)) + MIN_CORRUPT
    for i in xrange(int(size * corrupt_pct) + 1):
        offsets.append(random.randint(0, size-1))
    offsets = sorted(offsets)

    # Open the input and output files
    inFile = open(sys.argv[2], "rb")
    outFile = open(sys.argv[3], "wb")

    # Loop copying data until the next offset is reached and pass that to the
    # function to mutate the data before writing it to the output
    nextOffset = offsets.pop(0)
    current = 0
    while current < size:
        # Copy data to output file
        if current < nextOffset:
            copyData(inFile, outFile, nextOffset-current)
            current = nextOffset

        # Choose a mutator
        mutator = random.choice(MUTATORS)

        # print "Fuzzing offset 0x%x with mutator %s" % (nextOffset,
        #     mutator.__name__)

        # Mutate data
        mutatedData = mutator(inFile)
        outFile.write(mutatedData)
        current += len(mutatedData)

        # Check if all offsets have been processed
        if len(offsets) == 0:
            break
        else:
            nextOffset = offsets.pop(0)

    copyData(inFile, outFile, size-current)

if __name__ == '__main__':
    main()
