#!/usr/bin/env python

import csv
import sys
import subprocess
import re
import datetime
import random
import tgrequest

filename = sys.argv[1]

with open(filename, 'rt') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL, skipinitialspace=True)

    for row in csvreader:

        if row[0] == "Input URI-R":
            continue # skip header row

        dt = row[1]
        uri_g_stem = row[2]
        uri_m = row[3]

        #uri_m = sys.argv[1]
        #uri_g_stem = sys.argv[2]
        #dt = sys.argv[3]
        # input dt format is MM/DD/YYYY HH:MM:SS
        #dt = datetime.datetime.strptime(dt, "%m/%d/%Y %H:%M:%S")
        dt = datetime.datetime.strptime(dt, "%a, %d %b %Y %H:%M:%S GMT")

        currentdate = datetime.datetime.now()
        rantime = tgrequest.randomDate("01/01/1997 00:00:00", currentdate.strftime("%m/%d/%Y %H:%M:%S"),
            random.random())

        #print(type(rantime))
        dt = datetime.datetime.strptime(rantime, "%m/%d/%Y %H:%M:%S")
        
        p = subprocess.Popen(['curl', '-v', '-I', uri_m], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        out, err = p.communicate()
        original = None

        pat = re.compile('<([^>]*)>;[ ]*rel="original"')
        
        for line in out.split('\n'):
            if 'Link:' == line[0:5]:
                original = pat.findall(line)[0]
                break
  
        if original:
            items = tgrequest.tgrequest(original, uri_g_stem, dt)[1:]
            items.insert(0, uri_m)
            print ','.join('"{0}"'.format(i) for i in items)
        else:
            print "NON-COMPLIANT Memento:  " + uri_m
