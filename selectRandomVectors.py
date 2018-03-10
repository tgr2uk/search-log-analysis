# randomly selects 100,000 lines from a file of AOL data of the form
# <queries>,<clicks>,<whatever>  - which could be filtered
# e.g. to remove values > 100

# usage: python selectRandomLines.py <inputfile> -s 100000 > <outputfile>

import random
import argparse
import sys
import re

n = 100000
charsToSkip = 8

parser = argparse.ArgumentParser()
parser.add_argument('inputFile', help='name of the input logfile')
parser.add_argument("-s", "--sampleSize", help="number of lines to select")
args = parser.parse_args()

sys.stderr.write("Inputfile =\t%s\n" % args.inputFile)
if args.sampleSize:
    n = args.sampleSize
    n = int(n)
    sys.stderr.write("Sample size = \t%d\n" % n)

with open(args.inputFile) as f:
    lines = random.sample(f.readlines(), n)


for line in lines:
    print line[charsToSkip:],        # skip the first N chars

sys.stderr.write("Done.\n")
