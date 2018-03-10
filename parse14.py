# parse a file of data in AOL log format
# splits lines that are marked as query+click into 2 lines: a query line
# (which is the first 3 fields) and a click line (which is the last 2 fields)
# This separates the click from its associated query. For consistency,
# regular click events (defined as a line with 5 fields where the query
# is repeated) are also displayed using just the last 2 fields.

# Usage: python parse14.py -v fullcollection.1000

# Output is a feature vector of the form:# queries, clicks, pages,
# allActions, duration, meanQLen, meanQInterval, meanTermUseFreq, meanTermPop

# meanTermUseFreq is more than simple TTR. Consider these queries:
# q1 = a a a b b c
# q2 = a a a a b c

# q2 is more homogeneous, so our freq measure should capture this.
# But TTR (q1) = TTR (q2) = 3/6 = 0.5
# By contrast, if we calciulate the meanTermUseFreq as
# meanTermUseFreq(q1) = ((3/6 * 3) + (2/6 * 2) + 1/6) / 6 = 0.388
# meanTermUseFreq(q2) = ((4/6 * 4) + 1/6 + 1/6) / 6 = 0.5
# If you expand the above the calculation becomes SUM(termFreq**2 / N**2)

# TermPopularity is calculated using the mean popularity
# of each *individual* query term

# TODO: 
# Re-run python pep8

import datetime
import time
import argparse
import sys
import logging
import re
import numpy
import csv
from collections import Counter

# GLOBALS:
logFileName = 'output.log'
# date example = 2006-03-24 20:51:24
format = "%Y-%m-%d %H:%M:%S"
# initialise the session variables and bin counters
numQueries = numClicks = numPages = numsessions = numLines = aveQLength = 0
q0c0 = q0c1 = q0cm = q1c0 = q1c1 = q1cm = qmc0 = qmc1 = qmcm = uncl = 0
qLens = []
sessionTerms = []
# initialise the global stats
totQueries = totClicks = totPages = 0
# set the term frequency list file
##tfFile = 'fullcollection.1000000.terms.csv'
tfFile = 'aoltermlist.csv'
# session timeout (in minutes)
timeout = 30


# Read a file of term frequencies (in csv format) and return it as a dict
def readTFL(tfFile):
    tfl = {}
    n = 0
    print >> sys.stderr, "Reading file %s..." % tfFile
    rdr = csv.DictReader(file(tfFile))
    for row in rdr:
        n += 1
        if ((n % 1000000) == 0):
            print "Read %d lines" % n
        tfl[row["query"]] = row["freq"]
    print >> sys.stderr, "Done."
    return tfl


# parse the individual lines in the log file
def parseLine():
    global items, rank, url, query, qPrevious, timeStamp
    global numQueries, numClicks, numPages, qLens, sessionTerms

    if (items[l-1] != '\n'):  # last item is more than /n, so it's a clickthru
        rank = items[3]
        url = items[4]
        if (query == qPrevious):  # same query means it's just a click (?)
            logging.info('<CLICK>\t%s\t%s\t%s\t%s', id, rank,
                         url.rstrip('\n'), timeStamp)
            numClicks += 1
        else:   # different query means it has to be composite query + click
            logging.info('<QRY?>\t%s\t%s\t%s', id, query, timeStamp)
            # calculate query length (non-whitespace strings)
            qLen = len(re.findall(r'\S+', query))
            qLens.append(qLen)  # add to list
            # append query to sessionTerms
            qTerms = re.split('\s+', query)
            for term in qTerms:
                sessionTerms.append(term)

            logging.info('<CLK?>\t%s\t%s\t%s\t%s', id, rank, url.rstrip('\n'),
                         timeStamp)
            numQueries += 1
            numClicks += 1
    else:   # it's a query or pagination
        if (query == qPrevious):
            logging.info('<PAGE>\t%s\t%s', id, timeStamp)
            numPages += 1
        else:
            logging.info('<QUERY>\t%s', line.rstrip())
            # calculate query length (non-whitespace strings)
            qLen = len(re.findall(r'\S+', query))
            qLens.append(qLen)  # add to list
            # append query to sessionTerms
            qTerms = re.split('\s+', query)
            for term in qTerms:
                sessionTerms.append(term)

            numQueries += 1


# identify the session category (i.e. q1c0 etc.) and output the feature vector
def calculateVector():
    global numsessions, numQueries, numClicks, numPages, duration, qLens, \
           sessionTerms
    global q0c0, q0c1, q0cm, q1c0, q1c1, q1cm, qmc0, qmc1, qmcm, uncl
    global totQueries, totClicks, totPages

    numsessions += 1
    meanTermUseFreq = 0
    meanTermPop = 0

    # calculate the mean query length for the session
    if qLens:
        meanQLen = numpy.mean(qLens)
    else:
        meanQLen = 0

    # calculate the mean query interval
    # TODO mean Q interval is the mean of all inter-query gaps, which is NOT
    # the same as the overall session duration divided by (num queries - 1)
    if (numQueries > 1):
        meanQInterval = duration.seconds / float(numQueries - 1)
    else:
        meanQInterval = 0

    # calculate the mean term use frequency
    if numQueries:
        sessionWFL = Counter(sessionTerms)
        logging.debug('sessionWFL is %s', sessionWFL)
        numTerms = sum(sessionWFL.values())
        logging.debug('numTerms = %d', numTerms)
        for item in sessionWFL:
            freq = sessionWFL[item]
            # each term contributes the square of its freq / N squared
            x = freq**2 / float(numTerms**2)
            logging.debug('item = %s, freq = %s, contrib = %3.2f', item, freq, float(x))
            meanTermUseFreq += x
        logging.debug('meanTermUseFreq = %3.2f', meanTermUseFreq)

    # calculate the mean term popularity
    if numQueries:
        totPop = 0
        for term in sessionTerms:
            pop = int(TFL[term])
            logging.debug('term = %s, pop = %s', term, pop)
            totPop += pop
        meanTermPop = totPop/float(len(sessionTerms))
        logging.debug('meanTermPop = %3.2f', meanTermPop)

    # output the basic feature vector
    allActs = numQueries + numClicks + numPages
    logging.warning('%d,%d,%d,%d,%d,%4.3f,%4.3f,%4.3f,%4.3f', numQueries, numClicks,
                    numPages, allActs, duration.seconds, meanQLen,
                    meanQInterval, meanTermUseFreq, meanTermPop)

    # determine the session type
    if (numQueries == 0):
        if (numClicks == 0):
            logging.info('</SESSION q0c0>\n')
            q0c0 += 1
        elif (numClicks == 1):
            logging.info('</SESSION q0c1>\n')
            q0c1 += 1
        elif (numClicks > 1):
            logging.info('</SESSION q0cm>\n')
            q0cm += 1
    elif (numQueries == 1):
        if (numClicks == 0):
            logging.info('</SESSION q1c0>\n')
            q1c0 += 1
        elif (numClicks == 1):
            logging.info('</SESSION q1c1>\n')
            q1c1 += 1
        elif (numClicks > 1):
            logging.info('</SESSION q1cm>\n')
            q1cm += 1
    elif (numQueries > 1):
        if (numClicks == 0):
            logging.info('</SESSION qmc0>\n')
            qmc0 += 1
        elif (numClicks == 1):
            logging.info('</SESSION qmc1>\n')
            qmc1 += 1
        elif (numClicks > 1):
            logging.info('</SESSION qmcm>\n')
            qmcm += 1
    else:
        logging.info('</SESSION UNCL>\n')
        uncl += 1
    logging.info('<SESSION>')  # print open session element to start next one

    # record the overall stats and reset the session variables
    totQueries += numQueries
    totClicks += numClicks
    totPages += numPages

    return (totQueries, totClicks, totPages)


# output the overall stats for each category in the log file
def printSessionStats():
    print "Numsessions = ", numsessions
    print "q0c0 = %3d, %3.1f%%\t" % (q0c0, q0c0*100/float(numsessions)),
    print "q0c1 = %3d, %3.1f%%\t" % (q0c1, q0c1*100/float(numsessions)),
    print "q0cm = %3d, %3.1f%%\t" % (q0cm, q0cm*100/float(numsessions))
    print "q1c0 = %3d, %3.1f%%\t" % (q1c0, q1c0*100/float(numsessions)),
    print "q1c1 = %3d, %3.1f%%\t" % (q1c1, q1c1*100/float(numsessions)),
    print "q1cm = %3d, %3.1f%%\t" % (q1cm, q1cm*100/float(numsessions))
    print "qmc0 = %3d, %3.1f%%\t" % (qmc0, qmc0*100/float(numsessions)),
    print "qmc1 = %3d, %3.1f%%\t" % (qmc1, qmc1*100/float(numsessions)),
    print "qmcm = %3d, %3.1f%%\t" % (qmcm, qmcm*100/float(numsessions))
    print "uncl = %3d, %3.1f%%\n" % (uncl, uncl*100/float(numsessions))


# output the stats for queries, clicks and pages
def printLogStats(queries, clicks, pages):
    print "Total # of queries = %3d" % queries
    print "Total # of clicks = %3d" % clicks
    print "Total # of pages = %3d\n" % pages


# MAIN STARTS HERE
# set up command line args parser
parser = argparse.ArgumentParser()
parser.add_argument('inputFile', help='name of the input file')
parser.add_argument("-v", "--vectors",
                    help="output feature vectors (only)",
                    action="store_true")
parser.add_argument("-t", "--transcript", help="output full session transcript",
                    action="store_true")
parser.add_argument("-d", "--debug", help="include debug messages",
                    action="store_true")
args = parser.parse_args()
if args.debug:
    logging.basicConfig(format='%(levelname)s:%(message)s',
                        filename=logFileName, level=logging.DEBUG)
elif args.transcript:
    logging.basicConfig(format='%(levelname)s:%(message)s',
                        filename=logFileName, level=logging.INFO)
elif args.vectors:  # default level is WARNING
    logging.basicConfig(format='%(levelname)s:%(message)s',
                        filename=logFileName, level=logging.WARNING)


# initialise the baseline time and userID
sessionStart = datetime.datetime.strptime("2006-03-01 07:17:12", format)
tPrevious = sessionStart
idPrevious = '142'
qPrevious = 'a test query'

startTime = time.time()
print "\nStart time =\t", time.asctime(time.localtime(startTime))
print "Inputfile =\t", args.inputFile
print "Logfile =\t", logFileName
print "Initial time =\t", tPrevious
print "Initial ID =\t", idPrevious
print "Initial query =\t", qPrevious, '\n'
logging.info('<SESSION>')

# Read the term popularity stats
# TFL = {}
TFL = readTFL(tfFile)
# Now test it:
for term in ['google', 'car', 'banana']:
    print >> sys.stderr, "Freq of %s is %d" % (term, int(TFL[term]))

##sys.exit()

with open(args.inputFile) as f:
    for line in f:
        numLines += 1
        if ((numLines % 100000) == 0):
            print "Processed %d lines" % numLines
        items = line.split('\t')
        l = len(items)
        if (items[0] == 'AnonID'):
            print >> sys.stderr, 'Skipping line number %d: %s' % (numLines,
                                                                  line)
            continue
        id = items[0]  # get the UserID
        query = items[1]   # get the query
        timeStamp = items[2]  # get the timestamp
        t = datetime.datetime.strptime(timeStamp, format)
        delta = (t - tPrevious).seconds/60
        # check whether it's the end of a session & if so what type
        if (delta >= timeout) or (id != idPrevious):   # it's the end of a session
            duration = tPrevious - sessionStart
            (totQueries, totClicks, totPages) = calculateVector()
            numQueries = numClicks = numPages = 0   # reset session variables
            sessionStart = t    # reset the session start to be current time
            del qLens[:]  # reset the list of query lengths
            del sessionTerms[:]  # reset the list of session terms

        # parse the line and format the output
        parseLine()
        # record the current line fields
        tPrevious = t
        idPrevious = id
        qPrevious = query
    logging.info('<EOF>\n')

printSessionStats()  # print the session stats (bin counts & percentages)
printLogStats(totQueries, totClicks, totPages)  # print the overall log stats

# check all the sums add up
assert numsessions == (q0c0 + q0c1 + q0cm + q1c0 + q1c1 + q1cm +
                       qmc0 + qmc1 + qmcm + uncl)

endTime = time.time()
elapsedTime = endTime - startTime
minutes, seconds = divmod(elapsedTime, 60)
print "Logfile =\t", logFileName
print "End time =\t", time.asctime(time.localtime(endTime))
print "Elapsed time =\t%d minutes %3.2f seconds" % (minutes, seconds)
