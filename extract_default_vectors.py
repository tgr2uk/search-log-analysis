# parse a file of data in AOL log format
# splits lines that are marked as query+click into 2 lines: a query line
# (which is just the first 3 fields) and a click line (which is the last 2 fields)
# this separates the click from its associated query. For consistency,
# regular click events (defined as a line with 5 fields where the query is repeated)
# are also displayed as just the last 2 fields.

# This version ignores lines beggining with 'AnonID', prints the elapsed time and
# supresses print statements

    # Usage: python extract_basic_vectors.py -s fullcollection.1000000
    # output goes to output.log which is of the form:
    # <logging level>1,0,0
    # i.e. queries, clicks, pages

# TODO
# Average query length
# Average position of clicked URLs
# Whether clicked URL matches query string
# Average time between queries


import datetime
import time
import argparse
import sys
import logging


def closeSession():
    global numsessions, numQueries, numClicks, numPages
    global q0c0, q0c1, q0cm, q1c0, q1c1, q1cm, qmc0, qmc1, qmcm, uncl
    global totQueries, totClicks, totPages, sessionDuration
    
    numsessions += 1
    # output the basic feature vector
    logging.warning('%d,%d,%d,%d', numQueries, numClicks, numPages, sessionDuration.total_seconds())
    numEvents = numQueries + numClicks + numPages
    # logging.warning('%2.3f,%2.3f,%2.3f', numQueries/float(numEvents), numClicks/float(numEvents), \
    #                numPages/float(numEvents))
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
    logging.info('<SESSION>')    # print an open session element to start the next one
    # record the overall stats and reset the session variables
    totQueries += numQueries
    totClicks += numClicks
    totPages += numPages
    numQueries = numClicks = numPages = 0   # reset the session variables
    return (totQueries, totClicks, totPages, sessionDuration)


def parseLine():
    global items, rank, url, query, qPrevious, time, timeStamp
    global numQueries, numClicks, numPages
    
    if (items[l-1] != '\n'): # last item is more than just /n, so it's a clickthrough event
        rank = items[3]
        url = items[4]
        if (query == qPrevious):  # same query means it's just a click(?)
            logging.info('<CLICK>\t%s\t%s\t%s\t%s', id, rank, \
                         url.rstrip('\n'), timeStamp)
            numClicks += 1
        else:   # different query means it has to be Q+C
            logging.info('<QRY?>\t%s\t%s\t%s', id, query, timeStamp)
            logging.info('<CLK?>\t%s\t%s\t%s\t%s', id, rank, url.rstrip('\n'), timeStamp)
            numQueries += 1
            numClicks += 1
            # TODO count query terms here?
    else:   # it's a query or pagination
        if (query == qPrevious):
            logging.info('<PAGE>\t%s\t%s', id, timeStamp)
            numPages += 1
        else:
            logging.info('<QUERY>\t%s', line.rstrip())
            numQueries += 1
            # Should we calculate query stats here?
            # NO: quicker & simpler to do outside of python, e.g. using sed, awk etc.
            # totQueryTerms= len(query.split())
            # logging.debug('query = %s', query)
            # logging.debug('Query length = %s', len(query.split()))

            
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


def printLogStats(terms, queries, clicks, pages):
    queryLength = terms/float(queries)
##    print "Total # of queries = %3d, total terms = %d, average length = %3.2f" % \
##            (queries, terms, queryLength)
    print "Total # of queries = %3d," % queries
    print "Total # of clicks = %3d" % clicks
    print "Total # of pages = %3d\n" % pages


# MAIN STARTS HERE
# set up command line args parser
logFileName = 'output.log'
parser = argparse.ArgumentParser()
parser.add_argument('inputFile', help='name of the input logfile')
parser.add_argument("-s", "--sessions", help="output session feature vectors",
                    action="store_true")
parser.add_argument("-l", "--log", help="output full session transcript",
                    action="store_true")
parser.add_argument("-d", "--debug", help="shows debug messages",
                    action="store_true")
args = parser.parse_args()
if args.debug:
    logging.basicConfig(filename=logFileName, level=logging.DEBUG)
elif args.log:
    logging.basicConfig(filename=logFileName, level=logging.INFO)
elif args.sessions:
    logging.basicConfig(filename=logFileName, level=logging.WARNING) # default level
    
# date example = 2006-03-24 20:51:24
format = "%Y-%m-%d %H:%M:%S"

# initialise the sessionStartTime, userID and query
sessionStartTime = tPrevious = datetime.datetime.strptime("2006-03-01 07:17:12", format)
idPrevious = '142'
qPrevious = 'a test query'

# initialise the session variables and bin counters
numQueries = numClicks = numPages = numsessions = numLines = 0 
q0c0 = q0c1 = q0cm = q1c0 = q1c1 = q1cm = qmc0 = qmc1 = qmcm = uncl = 0

# initialise the global stats 
totQueryTerms = totQueries = totClicks = totPages = sessionDuration = 0

startTime = time.time()
print "\nStart time =\t", time.asctime(time.localtime(startTime))
print "Inputfile =\t", args.inputFile
print "Logfile =\t", logFileName
print "Initial time =\t", tPrevious
print "Initial ID =\t", idPrevious
print "Initial query =\t", qPrevious, '\n'
logging.info('<SESSION>')

with open(args.inputFile) as f:
    for line in f:
        numLines += 1
        if ((numLines%100000) == 0):
            print "Processed %d lines" % numLines
        items = line.split('\t')
        l = len(items)
        if (items[0] == 'AnonID'):
            print >> sys.stderr, 'Skipping line number %d: %s' % (numLines, line)
            continue
        id = items[0]  # get the UserID
        query = items[1]   # get the query        
        timeStamp = items[2] # get the timestamp
        t = datetime.datetime.strptime(timeStamp, format)
        delta = (t - tPrevious).seconds/60
        # if it's a new session, close the old one
        if (delta >= 30) or (id != idPrevious):   # it's a new session
            sessionDuration = tPrevious - sessionStartTime
            (totQueries, totClicks, totPages, sessionDuration) = closeSession()
            sessionStartTime = t

        # parse the line and format the output
        parseLine()
        # record the current feature values
        tPrevious = t
        idPrevious = id
        qPrevious = query
    logging.info('<EOF>\n') # TODO really ought to check what type of session it is here

printSessionStats() # print the session stats (bin counts & percentages)
printLogStats(totQueryTerms, totQueries, totClicks, totPages) # print the overall stats for the log file

# check all the sums add up
assert numsessions == (q0c0 + q0c1 + q0cm + q1c0 + q1c1 + q1cm + \
                       qmc0 + qmc1 + qmcm + uncl)

endTime = time.time()
elapsedTime = endTime - startTime
minutes, seconds= divmod(elapsedTime, 60)
print "Logfile =\t", logFileName
print "End time =\t", time.asctime(time.localtime(endTime))
print "Elapsed time =\t%d minutes %3.2f seconds" % (minutes, seconds)


