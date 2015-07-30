#!/usr/bin/env python
""" CLI audio file mixer.

    License: http://www.gnu.org/licenses/gpl-3.0.en.html
"""

import argparse
import math
import os
import random
import shutil
try:
    import wavefile
except ImportError:
    print("Error:  Missing Python module 'wavefile', please install")
    exit(1)
try:
    import numpy
except ImportError:
    print("Error:  Please install Numpy")

def lin_to_db(a_value):
    if a_value >= 0.001:
        return math.log(float(a_value), 10.0) * 20.0
    else:
        return -120.0

def db_to_lin(a_value):
    return pow(10.0, (0.05 * float(a_value)))

parser = argparse.ArgumentParser(
    description="CLI audio file mixer, see "
    "https://github.com/j3ffhubb/python-mix")
parser.add_argument(
    "-n", "--normalize", dest="normalize", default=None, type=float,
    help="Normalize the mixed file to this decibel value, should be in "
    "the range of 0 to -24")
parser.add_argument(
    "files", type=str, nargs="+",
    help="output.wav file1.wav file2.wav, ..., see the "
    "libsndfile documentation for supported formats")
ARGS = parser.parse_args()

if len(ARGS.files) < 2:
    print("Error:  No files specified")
    exit(1)
if len(ARGS.files) == 2 and ARGS.normalize is None:
    print("Error:  Only one file specified")
    exit(1)

OUTPUT_FILE = ARGS.files[0]
FILES = ARGS.files[1:]
MISSING = [x for x in FILES if not os.path.isfile(x)]

if MISSING:
    print("Error:  Missing files: {0}".format(MISSING))
    exit(1)

SIZE = (1024 * 1024)
INPUT = [wavefile.WaveReader(x) for x in FILES]
GENERATORS = [(x, x.read_iter(SIZE)) for x in INPUT]
SAMPLE_RATES = set(x.samplerate for x in INPUT)

if len(SAMPLE_RATES) != 1:
    print("Error:  Multiple sample rates {0} not yet "
        "supported".format(tuple(SAMPLE_RATES)))
    exit(1)

SR = tuple(SAMPLE_RATES)[0]
MAX = 0.0

with wavefile.WaveWriter(OUTPUT_FILE, channels=2, samplerate=SR) as writer:
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
        buffer_max = numpy.amax(numpy.abs(BUFFER))
        if buffer_max > MAX:
            MAX = buffer_max
        writer.write(BUFFER)

print("Created {0}".format(OUTPUT_FILE))
print("Maximum amplitude {0}dB".format(round(lin_to_db(MAX), 1)))


if ARGS.normalize is not None:
    if MAX < 0.03:
        print("Error:  The amplitude is too low to normalize")
        exit(0)
    print("Normalizing...")
    norm_lin = db_to_lin(ARGS.normalize)
    amp_multiplier = norm_lin / MAX
    print("Amp. multiplier: {0}".format(amp_multiplier))
    randint = str(random.randint(1000000, 9999999))
    tmp = "".join([OUTPUT_FILE.rsplit('.', 1)[0], '-tmp-', randint, '.wav'])
    shutil.move(OUTPUT_FILE, tmp)
    with wavefile.WaveWriter(OUTPUT_FILE, channels=2, samplerate=SR) as writer:
        with wavefile.WaveReader(tmp) as reader:
            for data in reader.read_iter(SIZE):
                writer.write(data * amp_multiplier)
    os.remove(tmp)
