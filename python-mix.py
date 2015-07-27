#!/usr/bin/env python

import os
import sys
try:
    import wavefile
except ImportError:
    print("Error:  Missing Python module 'wavefile', please install")
    exit(1)
try:
    import numpy
except ImportError:
    print("Error:  Please install Numpy")

if len(sys.argv) < 4:
    print("Usage: {0} output_file file1 file2 ...".format(__file__))
    exit(1)

OUTPUT_FILE = sys.argv[1]
FILES = sys.argv[2:]
MISSING = [x for x in FILES if not os.path.isfile(x)]

if MISSING:
    print("Error:  Missing files: {0}".format(MISSING))
    exit(1)

SIZE = (1024 * 1024) # Read 1MB chunks from the files
INPUT = [wavefile.WaveReader(x) for x in FILES]
GENERATORS = [(x, x.read_iter(SIZE)) for x in INPUT]

with wavefile.WaveWriter(OUTPUT_FILE, channels=2) as writer:
    while GENERATORS:
        BUFFER = numpy.zeros((2, SIZE))
        for fh, gen in GENERATORS[:]:
            try:
                data = next(gen)
            except StopIteration:
                GENERATORS.remove((fh, gen))
                fh.close()
                continue
            if fh.channels == 1:
                for i in range(2):
                    BUFFER[i,:data.shape[1]] += data[0]
            else:
                BUFFER[:,:data.shape[1]] += data
        writer.write(BUFFER)

print("Created {0}".format(OUTPUT_FILE))
