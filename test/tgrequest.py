#!/usr/bin/env python

import sys
import subprocess
import datetime
import random
import time

# stolen from http://stackoverflow.com/questions/553303/generate-a-random-date-between-two-other-dates
def strTimeProp(start, end, format, prop):
    """Get a time at a proportion of a range of two formatted times.

    start and end should be strings specifying times formated in the
    given format (strftime-style), giving an interval [start, end].
    prop specifies how a proportion of the interval to be taken after
    start.  The returned time will be in the specified format.
    """

    stime = time.mktime(time.strptime(start, format))
    etime = time.mktime(time.strptime(end, format))

    ptime = stime + prop * (etime - stime)

    return time.strftime(format, time.localtime(ptime))


def randomDate(start, end, prop):
    return strTimeProp(start, end, '%m/%d/%Y %H:%M:%S', prop)

# now the "original" code

def tgrequest(uri_r, uri_g_stem, dt):

    #print "args: " + str(len(sys.argv))
    
    dt = dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
    
    print('Command:  curl -v -I -L -H "Accept-Datetime: ' + dt + '" ' + uri_g_stem + uri_r)
    
    # curl -v -I -L -H "Accept-Datetime: $dt" ${URIG}${URIR}
    p = subprocess.Popen(['curl', '-v', '-I', '-L', '-H', 'Accept-Datetime: ' + dt, uri_g_stem + uri_r],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    
    uris = []
    
    for line in err.split('\n'):
        #print line
        if 'Issue another request to this URL' in line:
            #print "FOUND IT:  " + line
            uri = line.replace("* Issue another request to this URL: '", '')
            uri = uri.rstrip("'")
            uris.append(uri)
            #print "APPENDING URI:  " + uri
    
    #print uris
    
    uri_m = uris.pop()
    
    items = []
    
    items.append(uri_r)
    items.append(dt)
    items.append(uri_g_stem)
    items.append(uri_m)

    return items

if __name__ == '__main__':

    if len(sys.argv) == 4:
        dt = sys.argv[3]
        # input dt format is MM/DD/YYYY HH:MM:SS
        dt = datetime.datetime.strptime(dt, "%m/%d/%Y %H:%M:%S")
    else:
        currentdate = datetime.datetime.now()
        rantime = randomDate("01/01/1997 00:00:00", currentdate.strftime("%m/%d/%Y %H:%M:%S"), random.random())
        #print(type(rantime))
        dt = datetime.datetime.strptime(rantime, "%m/%d/%Y %H:%M:%S")

    items = tgrequest(sys.argv[1], sys.argv[2], dt)
    print ','.join('"{0}"'.format(i) for i in items)
