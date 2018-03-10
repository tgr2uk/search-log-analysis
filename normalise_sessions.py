# normalises a file of AOL session vectors using feature scaling
# usage: python normalise_sessions.py 100000.sample1.arff > 100000.sample1.norm.arff

# Output is a feature vector of the form:
# queries, clicks, pages, allActions, duration, meanQLen, meanQInterval, meanTermFreq


import argparse
import numpy as np
import sys

parser = argparse.ArgumentParser()
parser.add_argument('inputFile', help='name of the input logfile')
args = parser.parse_args()

queries = []
clicks = []
pages = []
actions = []
durations = []
qLens = []
qIntervals = []
termFreqs = []
queryPops = []
lines = 0

with open(args.inputFile) as f:
    for line in f:
        items = line.split(',')
        l = len(items)
        if (l < 3):     
            # skip the non-data lines
            continue
        queries.append(int(items[0]))
        clicks.append(int(items[1]))
        pages.append(int(items[2]))
        actions.append(int(items[3]))
        durations.append(int(items[4]))
        qLens.append(float(items[5]))
        qIntervals.append(float(items[6]))
        termFreqs.append(float(items[7]))
        queryPops.append(float(items[8]))
        lines += 1

meanQ = np.mean(queries)
meanC = np.mean(clicks)
meanP = np.mean(pages)
meanA = np.mean(actions)
meanD = np.mean(durations)
meanQL = np.mean(qLens)
meanQI = np.mean(qIntervals)
meanTF = np.mean(termFreqs)
meanQP = np.mean(queryPops)

sdQ = np.std(queries)
sdC = np.std(clicks)
sdP = np.std(pages)
sdA = np.std(actions)
sdD = np.std(durations)
sdQL = np.std(qLens)
sdQI = np.std(qIntervals)
sdTF = np.std(termFreqs)
sdQP = np.std(queryPops)

print >> sys.stderr, "mean queries = %3.2f, std dev = %3.2f" % (meanQ, sdQ)
print >> sys.stderr, "mean clicks = %3.2f, std dev = %3.2f" % (meanC, sdC)
print >> sys.stderr, "mean pages = %3.2f, std dev = %3.2f" % (meanP, sdP)
print >> sys.stderr, "mean actions = %3.2f, std dev = %3.2f" % (meanA, sdA)
print >> sys.stderr, "mean durations = %3.2f, std dev = %3.2f" % (meanD, sdD)
print >> sys.stderr, "mean qLens = %3.2f, std dev = %3.2f" % (meanQL, sdQL)
print >> sys.stderr, "mean qIntervals = %3.2f, std dev = %3.2f" % (meanQI, sdQI)
print >> sys.stderr, "mean TermFreqs = %3.2f, std dev = %3.2f" % (meanTF, sdTF)
print >> sys.stderr, "mean queryPops = %3.2f, std dev = %3.2f" % (meanQP, sdQP)

# now write them out as normalised vectors
with open(args.inputFile) as f:
    for line in f:
        items = line.split(',')
        l = len(items)
        if (l < 3):
            # just print the non-data lines as is
            print line,
        else:
            normQueries = (int(items[0]) - meanQ) / sdQ
            normClicks = (int(items[1]) - meanC) / sdC
            normPages = (int(items[2]) - meanP) / sdP
            normActions = (int(items[3]) - meanA) / sdA
            normDurations = (int(items[4]) - meanD) / sdD
            normQLens = (float(items[5]) - meanQL) / sdQL
            normQIntervals = (float(items[6]) - meanQI) / sdQI
            normTermFreqs = (float(items[7]) - meanTF) / sdTF
            normQueryPops = (float(items[8]) - meanQP) / sdQP
            print "%3.3f, %3.3f, %3.3f, %3.3f, %3.3f, %3.3f, %3.3f, %3.3f, %3.3f" % \
                  (normQueries, normClicks, normPages, normActions,
                   normDurations, normQLens, normQIntervals, normTermFreqs,
                   normQueryPops)

print >> sys.stderr, "Done"
