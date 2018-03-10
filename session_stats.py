# calculates the mean and std deviation of a file of session vectors

import argparse
import numpy

parser = argparse.ArgumentParser()
parser.add_argument('inputFile', help='name of the input logfile')
args = parser.parse_args()

queries = clicks = pages = lines = 0
meanQ = meanC = meanP = 0

with open(args.inputFile) as f:
    for line in f:
        items = line.split(',')
        l = len(items)
        if (l < 3):
            # skip the non-data lines
            continue
        queries += int(items[0])
        clicks += int(items[1])
        pages += int(items[2])
        lines += 1

print "queries = %d, clicks = %d, pages = %d, lines = %d" % (queries, clicks, pages, lines)
meanQ = queries/float(lines)
meanC = clicks/float(lines)
meanP = pages/float(lines)
print "mean queries = %3.2f , mean clicks = %3.2f, mean pages = %3.2f" % (meanQ, meanC, meanP)

