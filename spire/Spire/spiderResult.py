# $Id: spiderResult.py,v 1.1 2012/07/03 14:21:59 leith Exp $
#
# functions for processing SPIDER results files

"""
SPIRE - The SPIDER Reconstruction Engine
Copyright (C) 2006-2008  Health Research Inc.

HEALTH RESEARCH INCORPORATED (HRI),
ONE UNIVERSITY PLACE, RENSSELAER, NY 12144-3455

Email:  spider@wadsworth.org

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.
"""
import sys
import string
import time
import os
import re
import GB
from spiderUtils import *
from spiderClasses import SpiderBatchRun, SpireoutParms

errstream = sys.stderr
outstream = sys.stdout

# get information from the top of the spireout file.
# Returns a SpireoutParms object.
def headSpireout(spireout):
    spireparms = SpireoutParms()  # create an object to hold results
    done = 0
    ntimes = 20
    nbytes = 280
    
    for i in range(ntimes):  # try reading the file up 20 times (until get pid)
        try:
            fp = open(spireout)
            s = fp.read(nbytes)   # read up to 280 bytes
            fp.close()
            if len(s) == 0:
                continue
            ss = s.split('\n')
            for line in ss:
                if line.find("Running") > -1:
                    runline = string.strip(line.replace("Running:", ""))
                    spireparms.runningline = runline
                    
                elif line.find("VERSION:") > -1:
                    v = line.find("VERSION:")
                    versionline = string.strip(line[v:])
                    a = line.find('UNIX')
                    b = line.find('ISSUED')
                    if a > -1 and b > -1 and b > a+4:
                        spiderversion = string.strip(line[a+4:b])
                        spireparms.version = spiderversion
                            
                elif line.find("DATE:") > -1:
                    t = string.split(line)
                    spireparms.starttime = t[-1]
                    spireparms.startdate = t[-3]
                           
                elif line.find("Current process id") > -1:
                    spireparms.pid = line.split(":")[-1].strip()
                    done = 1
            if done:
                break
        except:
            GB.outstream('Unable to open %s\n' % (spireout))

    """
    print "----- headSpireout:"
    print spireparms.runningline
    print spireparms.version
    print spireparms.starttime
    print spireparms.startdate
    print spireparms.pid
    print "----- end spireparms"
    """
    
    if spireparms.pid == "":
        return 0
    else:
        return spireparms

def tailSpireout(spireout):
    if not os.path.exists(spireout):
        GB.errstream("tailSpireout: cannot find %s" % spireout)
        return ()
    cmd = 'tail -5 ' + spireout
    out = getCommandOutput2(cmd)
    if len(out) < 1:
        errstream.write('Unable to read ' + spireout)
        return ()
    B = string.split(out,'\n')
    time_end = ()
    for t in B:
        if t.find("COMPLETED") > -1 or t.find("TERMINATED") > -1:
            tr = string.split(t)
            time_end = (tr[-3],tr[-1])
            break
    if len(time_end) == 0:
        t = nowisthetime()
        time_end = (t[0],t[1])
    return time_end

# get the last few lines of the results file, up to the first
# .OPERATION line
def tailResults(resultsfile):
    if type(resultsfile) == type("string"):
        # input is the results filename; get the last 50 lines
        filename = resultsfile
        cmd = 'tail -50 ' + filename
        if not os.path.exists(filename):
            print "tailResults: cannot find %s" % filename
            return []
        out = getCommandOutput2(cmd)
        if len(out) < 1:
            errstream.write('Unable to read ' + filename)
            return []
        B = string.split(out,'\n')
    elif type(resultsfile) == type(["list"]):
        B = resultsfile

    n = len(B)
    R = []
    k = -1
    for i in range(n):
        line = B[k]
        #print "tailResults %s" % (line)
        R.append(line + '\n')
        k = k-1
        if string.find(line,".OPERATION") > -1:
            break
    R.reverse()            
    return R

# returns tuple with date, time strings ("16-SEP-2003", "11:07:50")
# looks for "   /     \\          DATE:     16-SEP-2003    AT  11:07:50"
def headResults(results):
    try:
        fp = open(results,'r')
    except IOError, e:
        errstream.write('Unable to read ' + results)
        return ()

    date = ""
    dataext = ""
    batfile = ""
    n = 50
    ptr = 0
    while ptr < n:
        s = string.strip(fp.readline()); ptr = ptr+1
        if string.find(s,'DATE:') > -1:
            break
    d = string.split(s)
    date = (d[-3],d[-1])
    
    while ptr < n:
        s = string.strip(fp.readline()); ptr = ptr+1
        if string.find(s,'DATA EXTENSION:') > -1:
            break
    d = string.split(s,":")
    dataext = (d[-1])
    
    while ptr < n:
        s = string.strip(fp.readline()); ptr = ptr+1
        if string.find(s,'START OF:') > -1:
            break
    d = string.split(s,":")[1]
    batfile = string.split(d)[0]
    
    fp.close()
    return ( date, dataext, batfile )

# ------------------------------------------------------------------

MAXSIZE  = 1000000   #10000000    # 10 Mb limit?
MAXLINES =   10000    #30000      # corresponds to ~ 1 MB/chunk ?

re_inline = re.compile('_{1,3}[0-9]{1,2}')

def get_line(B, ptr):
    return B[ptr].strip()

# -----------------------------------------------------------------------
# Gets information about batch file from top of results file
# B = text from results file
def getBatchData(B):
	nlines = len(B)

	ptr = 0	
	while ptr < nlines:
		line = get_line(B, ptr)  
		if string.find(line, 'DATE:') > -1:
			t = string.split(line)
			bat_time = t[-1]
			bat_date = t[-3]
			break
		ptr = ptr + 1

	"""
	while ptr < nlines:
		line = get_line(B, ptr)  
		if string.find(line, 'EXTENSION:') > -1:
			t = string.split(line)
			batch_ext = t[2]
			data_ext  = t[5]
			break
		ptr = ptr + 1
	
	while ptr < nlines:
		line = get_line(B, ptr)  
		if string.find(line, 'START OF:') > -1:
			t = string.split(line)
			batch_file = t[3]
			break
		ptr = ptr + 1

	return [ batch_file, batch_ext, data_ext, bat_date, bat_time]
        """
	return [ bat_date, bat_time]

# -----------------------------------------------------------------------
# In: [list of [filenames, date, time] ]
# Out: [ filename, type, size, date, time ]
def docData(dlist):
    D = []
    for d in dlist:
	filename = d[0]
	ftype = "Document"

	if not os.path.exists(filename):
            continue

        nbytes = str(os.stat(filename)[6])
        # get docfile size only if has Spider data extension
        base,ext = os.path.splitext(filename)
        ext = ext[1:]
        if ext == GB.P.dataext:
            # get last key
            lastkey = None
            cmd = 'tail ' + filename
            tt = getCommandOutput2(cmd) # tail of doc file
            a = tt.split('\n')
            a.reverse()
            for i in a:
                if i != "" and i[1] != ";":
                    lastkey = i.split()[0]
                    break
        else:
            # has some other extension (.gnu, .pdf, etc.)
            lastkey = "0"
	f = [ filename, ftype, (lastkey,nbytes), d[1], d[2] ]
	D.append(f)
	
    return D

# -----------------------------------------------------------------------
# Filenames in results file may or may not have data extension.
# Add ext if not present. Needed when checking for deleted files.
# Sep 05: ANY extension will suffice (.gnu, etc)
def checkExt(file, ext):
    if ext[0] != '.':
        ext = '.' + ext
    if file == "plotview.gnu":
        print "checkExt : %s" % file
    filext = os.path.splitext(file)[1]
    
    if filext != '':   # ext is present
	return file
    else:
	return file + ext

# header is a concatenated string, not a list
# returns results filename
def getResultsFilename(header):
    # get the actual results filename
    if type(header) == type("string"):
        lines = header.split('\n')
    elif type(header) == type([]):
        lines = header
    else:
        print "spiderResult:getResultsFilename: argument must be string or list"
        print header
        return ()
    
    results = ""
    for line in lines:
        if line.find("Results file") > -1:
            if line.find(":") > -1:
                t = line.split(':')
                if len(t) > 1:
                    results = t[1].strip()
                    break   # avoid the line "Results file omitted for speed"
    return results

# for lines written by TS F: plotview  WRITTEN  13-SEP-2005 at 05:00:17
# TS F no longer in SPIDER 2/07
re_tsfile = re.compile("WRITTEN +\d\d-[A-Z][A-Z][A-Z]-\d\d\d\d at \d\d:\d\d:\d\d")

"""
Feb 2007, the following types are described in LUNSAYINFO in lunsethdr.f

Image         : (R ) X Y CREATED   ..... HEADER BYTES
Volume        : (R3) X Y Z CREATED
2D Fourier    : (E2/O2) X Y    (***** or could be a stack of 2D Fouriers ****)
3D Fourier    : (E3/O3) X Y Z  (***** or could be a stack of 3D Fouriers ****)
Image stack   : (S2) X Y ...
Volume stack  : (S3) X Y Z
Indexed stack : (I2) X Y
Indexed stack : (I3) X Y Z

or put another way
    stacks : S2, S3, I2, I3
      data : R, R3
    either : E2,E3,O2,O3
which is why the isStack flag is passed into getDataTuple

"""

TypeDict = { 'R': 'Image',
             'R3': 'Volume',
             'E2': '2D Fourier',
             'O2': '2D Fourier',
             'E3': '3D Fourier',
             'O3': '3D Fourier'}

StackTypes = {'E2': 'Fourier Stack',
              'O2': 'Fourier Stack',
              'E3': 'Fourier Stack',
              'O3': 'Fourier Stack',
              'S2': '2D Stack',
              'S3': '3D Stack',
              'I2': '2D Stack',
              'I3': '3D Stack'}

def getDataTuple(s, isStack=0, prev=""):
    " s is a line for binary files from spireout, of the form:  "
    " (R ) 75 75 CREATED 13-FEB-2007 AT 13:04:16  N HEADER BYTES: 1200 "
    " returns [type, size, date, time] "
    # prev (previous_line) added for debugging 
    xtype = s[1:3].strip()
    if isStack and xtype in StackTypes:
        type = StackTypes[xtype]
    elif xtype in TypeDict:
        type = TypeDict[xtype]
    else:
        type = 'Unknown'
        print "spiderResult.getDataTuple: type %s not recognized" % xtype
        print prev
        print s
        return [0, (0,0), "", ""]

    dim = 2
    if len(xtype) > 1:
        dim = int(xtype[1])
        
    t = s[4:].split()
    if len(t) < 7:
        print "spiderResult.getDataTuple: unable to get date/time"
        print s
        return [0, (0,0), "", ""]

    if dim == 2:
        size = (t[0],t[1])
    elif dim == 3:
        size = (t[0],t[1],t[2])
    else:
        size = ('size not found')
        print "spiderResult.getDataTuple: size not found"
        print s
        return [0, (0,0), "", ""]

    # assumes end of string has following format :
    # " .... CREATED 09-FEB-2007 AT 09:57:13  N HEADER BYTES:   1184"
    date = t[-7]
    time = t[-5]

    return [type, size, date, time]

def printDD(d):
    keys = d.keys()
    keys.sort()
    for k in keys:
        print k
        #print "%s: %s" % (k, str(d[k]))

# -----------------------------------------------------------------------
# B = text from results (spireout) file
# N = [ batch_file, batch_ext, data_ext, bat_date, bat_time]

# returns [DocFileList, BinFileList]

def processResult(B,datext):
    if datext[0] != '.':
        datext = '.' + datext
    nlines = len(B)
    BinFileList = []
    DocFileList = []
    bflist = []  # ordered list of filenames, contains names of deleted files
    dclist = []
    ptr = 1
    previous_line = ""
    StackDict = {}
    BinDict = {}   # holds file tuple info, DELETE files are removed from it

    while ptr < nlines:
	line = B[ptr].strip()

	# ------- look for new binary files (with 'N HEADER' ) -------
	# spire-1.5.1 : no longer checks if the binary file is already
	# in the dictionary. ANY time a file is rewritten (by CP or any
	# command) the N HEADER line appears. spire now keeps updating
	# dictionary every time a file appears, so that the project will
	# contain the last version. A separate dictionary is kept for
	# stacks, because the vast majority of stack calls are just
	# inserting stack elements.
	if line.find('N HEADER') > -1:
            fname = ""
	    previous_line = B[ptr-1].strip()

	    istk = previous_line.find('@')    # check if it's a stack
	    if istk > -1:
                isStack = 1
                fname = previous_line[:istk]
            else:
                isStack = 0
                fname = previous_line
                
            if fname[-4:] != datext:
                fname += datext
	    
            if not isStack: 
                # getDataTuple returns [type, size, date, time]
                newdata = getDataTuple(line, isStack, previous_line)
                if newdata[0] == 0:
                    #print "ptr is %d out of %d" % (ptr, nlines)
                    ptr = ptr + 1
                    continue
                else:
                    BinDict[fname] = [fname] + newdata
                    bflist.append(fname)
                
	    elif isStack:
                if fname not in StackDict:
                    newdata = getDataTuple(line, isStack, previous_line)
                    if newdata[0] == 0:
                        ptr = ptr + 1
                        continue
                    else:
                        StackDict[fname] = "" #######[fname] + newdata
                        BinDict[fname] = [fname] + newdata
                        bflist.append(fname)
                else:
                    fname = ""  # skip if the stack is already in StackDict
                    
            else:
                fname = ""
                    
            if fname == "":
                ptr = ptr + 1
                continue
		
	# ---------- look for new doc files -----------
	elif line.find('NEW DOC FILE') > -1:
            #print "processResult: " + line
	    t = line.split()
            # "09-FEB-2007 AT 09:57:13    OPENED NEW DOC FILE: tmp/doc001.dat"
	    docfile, docdate, doctime = t[-1],t[0],t[2]
	    if docfile[-4:] != datext: docfile += datext
	    DocFileList.append([docfile, docdate, doctime])
	    dclist.append(docfile)

	# ---------- check for deleted files ------------
	elif line.find('.DELETE FILE:') > -1:
	    delfile = line.split(':')[-1].strip()
	    if delfile[-4:] != datext: delfile += datext

	    if delfile in dclist:
		idx = dclist.index(delfile)
		dclist.remove(delfile)
		del DocFileList[idx]
		
	    elif delfile in BinDict:
                del(BinDict[delfile])
		# not necessary? => bflist.remove(delfile)
		if delfile in StackDict:
                    del(StackDict[delfile])
            
        ptr = ptr + 1
        # ---------- end: while ptr < nlines --------------------

    # now use bflist to create BinFileList
    # (files only deleted from BinDict, but only bflist retains file order
    for bf in bflist:
        if bf in BinDict:
            BinFileList.append(BinDict[bf])
            del(BinDict[bf])
	
    return [DocFileList, BinFileList]

# -----------------------------------------------------------------------
# This version checks for large results files and breaks them into chunks
#
# returns [doc list, binary list ]

def newOutputs(filename):
    if os.path.exists(filename):
        size = os.stat(filename)[6]    # get the size of the results file
    else:
        GB.errstream("Unable to find %s", filename)
        print os.getcwd()
        return [[],[]]

    if size < MAXSIZE:
	B = fileReadLines(filename)
	#N = getBatchData(B) # returns [batch_name,batext,datext,date,time]
	P = processResult(B,GB.P.dataext)
	BinList = P[1]
	DocList = P[0]
    else:
	done = 0
	BinList = []
	DocList = []
	FirstTime = 1
	
	try:
	    fp = open(filename,'r')
	except IOError, e:
	    print e

	while done == 0:    # loop over the chunks
	    B = []
	    for i in range(MAXLINES):
		line = fp.readline()
		if line:
		    B.append(line)
		else:
		    done = 1
		    break
					
	    if FirstTime == 1:
		FirstTime = 0
		N = getBatchData(B)
				
	    P = processResult(B,GB.P.dataext)
	    blist = P[1]
	    if len(blist) > 0: BinList = BinList + blist
	    dlist = P[0]
	    if len(dlist) > 0: DocList = DocList + dlist
			
	fp.close()

    DocList = docData(DocList)

    return [DocList, BinList]

if __name__ == '__main__':

    GB.outstream = GB.Output()
    GB.errstream = GB.Output()

    if len(sys.argv[1:]) > 0:
        br = readResults(sys.argv[1])

        for item in br.outfiles:
            print item
