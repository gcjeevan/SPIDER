# $Id: spiderBatch.py,v 1.1 2012/07/03 14:21:59 leith Exp $
#
# Controls execution of spider processes
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

import os, popen2, fcntl, select, sys
import string, time
import threading
import types
from commands import getoutput

import GB, GG
from spiderUtils import *
from spiderGUtils import *
from spiderExecwin import mkExecWindow, execBatchCleanup
from spiderFilenums import *
import spiderResult
import spiderRemote
import spiderReplace
from spiderClasses import SpiderBatchRun, threadObject
from spiderParam import replaceTagwithParam
#import spiderMain 

#-------------------------------------------------------------------
# runbatch( [dir, [batlist]] )
# input: a list of (string, list) pairs. Strings are taken as directories,
# lists as batch files. eg, [ (dir, [bat]), (dir, [bat, bat]) ]
# The program changes to each directory, and runs the batch files in
# the subsequent list.
# Starts batchLoop, then returns control to the GUI
#
def runbatch(runarg):
    # if runarg has only 2 things and 1st is a string, put them in a tuple
    if len(runarg) == 2 and type(runarg[0]) == type("string"):
        #print "runarg has %s, and %s" % (str(runarg[0]), str(runarg[1]))
        runarg = [(runarg[0], runarg[1])]

    """    
    runarg = [('.', ['bat01.bat']),
              ('Power', ['bat02.bat']),
              ('Power', ['bat03.bat'])]
    runarg = [('.', ['bat01.bat']),
              ('Power', ['bat02.bat','bat03.bat']),
              ('Corr', ['bat04.bat','bat05.bat'])]
    """
    #print "runbatch: " + str(runarg)     

    bloop = batchLoop(runarg=runarg)
    bloop.start()
    #bloop.run()

# priorRun : only checks if file numbers were run by same batch file.
#            Doesn't check filenames
# Quick check if any output files have the same numbers.
# Returns '1' as soon as it finds a match (= batch file already run).
def priorRun(batdir, batfile):
    #print "priorRun checking %s %s" % (batdir, batfile)
    if len(GB.P.RunList) == 0: return 0
    for id in GB.P.RunList:
        run = getBatchRun(id, outputs=1)
        if run == 0: continue
        dir = run.dir
        file = run.batfile
        #print dir, file
        if dir == batdir and file == batfile:
            fn = run.filenumbers # file numbers from batch file run
            f1 = range2list(fn)
            fn = getFileNumbers()
            if fn != None and fn != "":
                f2 = range2list(fn)
                for item in f2:
                    if item in f1:
                        return 1
    return 0

def updateFileOutputs(idnew, withoutputs=1):
    if len(GB.P.RunList) < 2: return
    newfiles = []
    newrun = getBatchRun(idnew, outputs=1)
    if len(newrun.outfiles) > GB.MaxNoFiles:
        GB.errstream("Too many files - aborting automatic updating")
        return
    #print dir(newrun)
    #print newrun.outfiles
    for item in newrun.outfiles:
        newfiles.append(item[0])
    newdir = newrun.dir
    newbat = newrun.batfile
    print "newfiles: " + str(newfiles)
    ids = GB.P.RunList
    for id in ids:
        if id == idnew:
            continue
        run = getBatchRun(id, outputs=1)
        if run.dir == newdir:
            if run.batfile == newbat:
                for item in run.outfiles:
                    if item[-1] == 'delete':
                        print "%s already deleted" % (item[0])
                        continue
                    oldfile = item[0]
                    if oldfile in newfiles:
                        print "%s has been overwritten" % (oldfile)
                        item.append('delete')
                        run.delete = 1
                        saveBatchRun(run)

#----------------------------------------------------------------
# batchLoop : runs a separate thread to monitor Spider process
# input arg = same as runbatch: [ (dir, [batlist]), (dir,batlist), .. ]
class batchLoop(threadObject):
    #def __init__(self, arg):
    #    self._stopevent = threading.Event()
    #    threading.Thread.__init__(self)
    #    self.runarg = arg
    #    self.prior_run = 0
        
    def run(self):
        if 'runarg' in self.kwargs:
            self.runarg = self.kwargs['runarg']
        stop = 0

        for item in self.runarg:
            if type(item) != type(("tuple",)):
                print "%s is not a tuple" % str(item)
                return
            
            batdir = item[0].strip()
            batlist = item[1]
            self.prior_run = 0
            thisThread = threading.currentThread()
            self.threadname = thisThread.getName()
            self.package.name = self.threadname
            
            b = []  # if runarg = ["b01,b02"], not ["b01", "b02"]
            for bf in batlist:
                if string.find(bf,",") > -1:
                    bl = string.split(bf,",")
                    for item in bl:
                        b.append(string.strip(item))
                else:
                    b.append(bf)
            batlist = b
            
            for batfile in batlist:
                # see if its not a batch file
                if batfile.find("<prog>") > -1:
                    prog = replaceTagwithParam(batfile)
                    GB.outstream("starting %s" % prog)
                    #################print "batdir: " + batdir
                    
                    if os.path.basename(GB.P.projdir) != os.path.basename(batdir):
                    	    execdir = os.path.join(GB.P.projdir,batdir)
                    else:
                    	    execdir = GB.P.projdir
                    if not os.path.samefile(os.getcwd(),execdir):   #,batdir):
                        os.chdir(execdir)   #(batdir)
                        
                    os.system(prog)
                    continue
                self.prior_run = 0
                if GG.sysprefs.checkPrior:
                    if priorRun(batdir, batfile):
                        if GG.prefs.delAsk:
                            msgtxt = "Some files may be overwritten.\n Continue?"
                            if not askOKorCancel(msgtxt, 'Warning'):
                                stop = 1
                                break
                        self.prior_run = 1
                        
                # this next line waits for the spider process to finish
                if GG.sysprefs.netexec == 'remote':
                    id = spiderRemote.execBatch(batdir, batfile)
                else:
                    id = execBatch(batdir, batfile)  # returns string or the int -1

                if str(id) == '-1':
                    stop = 1
                    break

                if self.prior_run:
                    GB.outstream( 'updating output files...\n')
                    updateFileOutputs(id)
            if stop:
                break

#--------------------------------------------------------
# an object for holding temporary values
class BatchRun:
    def __init__(self):
        self.pid = ""   # process ID
        self.batfile = ""
        self.dir  = ""
        self.host = ""
        self.time_start = ("","")  # tuple (date, time)
        self.time_end = ("","")    # e.g., ("21-SEP-2003", "03:44:15")
        self.date = ""
        #self.deleteResult = 0
        self.projID = ""
        self.results = ""
        self.filenumbers = ""
        self.filenumfile = ""
        self.script = ""
        self.reshdr = ""
        self.resultfile = ""
        self.spireout = ""
        self.spderr = ""
        self.spiderversion = '0.0'
        self.spidercmd = "none"
        self.kill = 0

def makeSpiderCommand(batfile, batargs=None, spider=None, dataext=None):
    runbat,ext = os.path.splitext(batfile)
    ext = ext[1:]   # remove dot from extension
    if spider == None:    spider = GG.sysprefs.spider  # name of executable
    if dataext == None:   dataext = GB.P.dataext
    if dataext[0] == '.': dataext = dataext[1:]

    if not batargs:
        cmd = "%s %s/%s SPIRE@%s &" % (spider, ext, dataext, runbat)
    else:
        if batargs[-1] == '&':
            batargs = batargs[:-1]
        args = stringify(batargs, sep=' ')
        cmd = "%s %s/%s SPIRE@%s %s &" % (spider, ext, dataext, runbat, args)
    return cmd
            
#--------------------------------------------------------

# ExecBatch runs batch files in the specified directory.
# If it completes successfully, it returns the run ID number (as a string),
# otherwise, it returns -1.
def execBatch(batdir, batfile):
    #GB.outstream( "execBatch1: %s, %s" % (batdir, batfile))
    if batdir == "" or batdir == None or batfile == "" or batfile == None:
        return -1
    if batdir == ".":
        batdir = GB.P.projdir
    #print "execBatch2: %s, %s" % (batdir, batfile)

    # are there Spider command line args? spider bat/dat @proc 1 loop=2 x=3 &
    bbb = batfile.split()
    if len(bbb) > 1:
        batfile = bbb[0]
        batargs = bbb[1:]
    else:
        batargs = []
    # create a class instance of BatchRun
    br = BatchRun()
    br.batfile = batfile
    br.dir = batdir
    br.projID = GB.P.ID
    br.host = GB.P.host      
    br.pid = "0"

    # get the thread name
    threadname = threading.currentThread().getName()
    n = threadname.find('-')
    threadno = int(threadname[n+1:])
    indent = '   ' * threadno
      
    batdir = os.path.basename(br.dir)
    if os.path.basename(GB.P.projdir) != os.path.basename(batdir):
        execdir = os.path.join(GB.P.projdir,batdir)
    else:
        execdir = GB.P.projdir
    
    if not chdir(execdir):
        print "execBatch: unable to chdir"
        return -1

    if not os.path.exists(batfile):
        displayError("Unable to find " + batfile)
        return -1
    
    # Save the original batch text
    originalBatch = fileReadLines(batfile)   #savecopy(batfile)
    #print "original batch in " + originalBatch

    # ----- Filenumbers ---------
    # if batch file uses file numbers,
    #    and if useFileNumbers is checked in preferences,
    #        and if Entry box not blank,
    #           then
    #              use Entry numbers
    #           else
    #              use filenums file
    #    else (not checked), just use filenums file
    #
    #    The filenums file is the filename associated with the filenumSymbol,
    #    (i.e., filename returned by getFilenumFilename)

    # check if batch file uses file numbers
    #useFileNums = useFileNumbers(os.path.join(execdir,batfile))
    filenumsFilename = getFilenumFilename(os.path.join(execdir,batfile))
    #print filenumsFilename
    if filenumsFilename != "":
        useFileNums = 1
    else:
        useFileNums = 0
    newfilenums = None
    filenumbers = None
    #defaultFilenumsFile = os.path.join(GB.P.projdir,GG.sysprefs.filenumFile)
    
    if useFileNums:
        # use values in the File Numbers entry box and temp filenum file
        if GG.prefs.useFilenumsEntry:
            filenumbers = getFileNumbersEntry() # check the entry box
                
            if filenumbers == None or filenumbers == "":
                if not os.path.exists(filenumsFilename):
                    txt = "No file numbers have been specified.\nContinue anyway?"
                    if not askOKorCancel(txt,"No file numbers!"):
                        return -1
            else:
                newfilenums = uniqueFilename(prefix='fn', extension=GB.P.dataext)
                filenumbers = readFileNumbers(filenumFile=newfilenums)  # writes entrybox to file
                br.filenumfile = newfilenums
                br.usingtmpfilenums = 1
                # change the filenumbers file in the batch file to tmp name
                ret = spiderReplace.batReplaceFilenums(batfile, filenumFile=newfilenums)
                if ret == 0:
                    GB.errstream("spiderBatch: unable to replace filenums file\n")
        else:
            # just use the filenums file
            if not os.path.exists(filenumsFilename):
                txt = "No file numbers have been specified.\nContinue anyway?"
                if not askOKorCancel(txt,"No file numbers!"):
                    return -1
            #filenumbers = readFileNumbers()  # writes to default filenums file
            
    #runbat,ext = os.path.splitext(batfile)
    #ext = ext[1:]   # remove dot from extension
    #spider = GG.sysprefs.spider  # name of executable
    #cmd = spider + " " + ext + "/" + GB.P.dataext + " SPIRE@" + runbat + " &"
    cmd = makeSpiderCommand(batfile, batargs)
    GB.outstream( "\nSending command: %s \n" % cmd)

    # create the execWindow
    ew = mkExecWindow(execdir, cmd, br)
    #print '%s******* %s: return from execWindow' % (indent,threadname)
    #print "%d active threads" % threading.activeCount()

    #############################################################
    #
    # ------- run SPIDER w/ code from getCommandOutput ----------
    #
    child = popen2.Popen3(cmd, 1) # Capture stdout & stderr from command
    #child = spiderMain.runPopen3(cmd)
    child.tochild.close()
    outfile = child.fromchild
    outfd = outfile.fileno()
    errfile = child.childerr
    errfd = errfile.fileno()
    pid = child.pid
    ######################## print "pid : " + str(pid)
    ew.insertpid(str(pid))
    
    makeNonBlocking(outfd)
    makeNonBlocking(errfd)
    outdata = errdata = ""
    outeof = erreof = 0

    gotresult = 0
    gotpid = 0   # from spireout
    versionline = "0"
    runningline = "0"
    spiderversion = "0.0"
    
    reshdr = ""
    docList = []
    binList = []
    outchunk = ""
    errchunk = ""
    pidlist = [pid]
    SPIDER_NORMAL_STOP = "SPIDER NORMAL STOP"
    # ---------------------------------------------------
    # hang out in while loop until Spider process is done
    while 1:
        # this part checks if the Spider process is still running
        #print 1,
        ready = select.select([outfd,errfd],[],[],.1)
        #print 2,
        #print child.poll(),  # ret -1 if not finished
        if outfd in ready[0]:
            outchunk = outfile.read()
            if outchunk == '': outeof = 1
            outdata += outchunk
            if not gotresult:
                reshdr = reshdr + outchunk
        if errfd in ready[0]:
            errchunk = errfile.read()
            if errchunk == '': erreof = 1
            errdata += errchunk
        if outeof and erreof:
            break
        # next section added because gnuplot forks were hanging Python
        """
        if SPIDER_NORMAL_STOP in errdata:
            sns = errdata.find(SPIDER_NORMAL_STOP)
            sns += len(SPIDER_NORMAL_STOP) # index to point after STOP
            if "  COMPLETED" in errdata[sns:]:
                break
        """
        #print 3,
            
        select.select([],[],[],.1) # Allow a little time for buffers to fill
        #print 4,

        ss = outdata.split('\n')
        #if ss != ['']: print ss
        
        # INITIAL IF : to get header and results filename
        # Spire gets spireout from results file from banner sent to stdout
        if not gotresult and outdata.find("Results file") > -1:
            #print "not gotresult, found results file in outdata"
            gotresult = 1
            hdr = []
            for line in ss:
                hdr.append(line)
                if line.find("Results file") > -1:
                    break
            for line in hdr:
                if line.find('\\\\') > -1:
                    line = line.replace('\\\\','\\')       
                GB.outstream(line)
    
            # get the actual results filename
            results = spiderResult.getResultsFilename(outdata)
            if results == "":
                displayError('Results file not found in output')
                execBatchCleanup(ew, success=0)
                fileWriteLines(batfile, originalBatch)
                return -1
            br.resultfile = results
            #print "calling insertres...",
            ew.insertres()
            #print "...back"
            # get the spireout file name, and read the header values
            spireout = results2spireout(results)
            sparms = spiderResult.headSpireout(spireout)
            if sparms:
                br.date = sparms.startdate
                br.time_start = (sparms.startdate, sparms.starttime)
                pid = sparms.pid
                if pid != "":
                    ew.insertpid(str(pid))

            outdata = ""
                
        # SUBSEQUENT IF : after the header and results filename,
        #                 just send Spider's stdout to the Main Window.
        elif gotresult:
            #print "got result"
            for line in ss:
                if line.strip() != "":
                    GB.outstream(line)
            outdata = ""
            
        try:
            id(ew)    # check if STOP button was pressed
        except:
            fileWriteLines(batfile, originalBatch)
            return -1

    # end hang out while loop
    # ---------------------------------------------------
    
    err = child.wait()
    if err != 0:
        print "spiderBatch: Popen.child returned with error"
        return -1
        #raise RuntimeError, 'failed with exit code %d\n%s' % (err, errdata)
    

    # process stderr (spderr) to get terminal condition (NORMAL|ERROR)
    spderr = errdata.split('\n')
    stopline = ""
    for line in spderr:
        if line.find("NORMAL") > -1:
            GB.outstream(line, 'green')
            stopline = line
        elif line.find("ERROR") > -1:
            GB.outstream(line, 'red')
            stopline = line
        else:
            GB.outstream(line)

    # restore the original batch file text
    fileWriteLines(batfile, originalBatch)

    # --------------------------------------------------------
    # Successful run - save results to batch run object
    #
    if stopline != "" and stopline.find(" NORMAL ") > -1: # success        
 
        if ew != None:
            try: ew.quit()
            except: pass

        GB.outstream(br.batfile + " finished successfully.")

        time_end = spiderResult.tailSpireout(spireout)
            
        # Successful run - create a batchRun object (sets b.id)
        #                  ========================
        b = SpiderBatchRun()
        # set default values
        b.id = makeRunID(br.time_start)
        b.batfile = batfile
        b.dir = batdir
        b.dataext = GB.P.dataext
        b.host = GB.P.host
        b.time_start = (sparms.startdate, sparms.starttime)
        b.time_end = time_end
        b.projID = GB.P.ID
        b.results = br.resultfile
        B = fileReadLines(batfile)
        b.text = B
        b.filenumbers = ""
        b.parameters = getParms()
        b.spiderversion = sparms.version
        b.spidercmd = [sparms.runningline, sparms.version]

        spireout = b.results.replace('results', 'spireout')

        if useFileNums and filenumbers != None:
            b.filenumbers = filenumbers

        #docList = spiderResult.docData(docList) # gets file sizes
        GB.outstream.write( 'Reading the spireout file %s...  ' % spireout) # no \n

        [doclist, binlist] = spiderResult.newOutputs(spireout)
        if len(doclist) == 0 and len(binlist) == 0:
            GB.outstream.write( ' no output files found.\n')
            execBatchCleanup(ew=ew, success=1)
            return -1
        GB.outstream.write( ' done.\n')
        b.outfiles = [doclist, binlist]

        #for ddd in doclist:
        #  print ddd
        #for ddd in binlist:
        #  print ddd
        
        nfiles = len(doclist) + len(binlist)
        if nfiles > 1: savetxt = "%d files from " % nfiles
        elif nfiles == 1: savetxt = "%d file from " % nfiles
        else: savetxt = ""
        savetxt += '%s saved to %s\n' % (br.batfile, GB.P.projfile)

        bat_id = saveBatchRun(b)
        # saveBatchRun may increment batch.id if it's already in the RunList,
        # which happens when successive batch runs finish in less than 1 sec.
        
        GB.outstream(savetxt)
        GG.spidui.write_queue('GG.topwindow.bell()') 

        if windowExists("Project Table") and hasattr(GG,'projectTable'):
            #GG.projectTable.addRow(batchrun=b)
            #GG.projectTable.table.see_last_row()
            func = GG.projectTable.addRow
            GG.spidui.write_queue([func, (b,)] )  # b = batchrun
            #GG.spidui.write_queue("self.testfunction()")
            GG.spidui.write_queue("GG.projectTable.seeLastRow()")

        if not int(GG.prefs.saveResults):
           delete(spireout)

        execBatchCleanup(ew=ew, success=1)
        return b.id      # *******  successful run  *******
            
    # --------------------------------------------------------
    # error in spider run 
    #
    else:
        GB.errstream("%s : error in spider run" % (batfile))
        GG.spidui.write_queue('GG.topwindow.bell()')
        GB.errstream(br.resultfile)
        GB.errstream(spderr)
    
        m = spiderResult.tailResults(br.resultfile)
        #print m
        for line in m:
            GB.outstream.write(line)
        execBatchCleanup(ew=ew, success=0)
        return -1
    
#
# ----- end of execBatch
#

def timeoutput(line):
    time_output_file = os.path.join(GB.P.projdir, 'timing.txt')
    fp = open(time_output_file, 'a')
    fp.write(line)
    fp.close()
    
##################################################################

# Returns when pid is no longer in pidlist.
# returns tuple: (year, mo, day, hr, min, sec, weekday, day#, dst)
def checkPid(pid, host):  # pid is a string
    sleeptime = 0.5 # seconds - put in GB

    while 1:
        time.sleep(sleeptime)
        pidlist = spiderRemote.getSpiderPID(host)
        if pid in pidlist:
            continue
        else:
            return pidlist
            #return time.localtime(time.time())

def readStdoutFile(spdfile):
    E = []
    if os.path.exists(spdfile):
        s = fileReadLines(spdfile)
        for line in s:
            d = string.replace(line, "\012", "\n")
            E.append(d)
    return E 
  

def runnit():
    runbatch(['Power_Spectra', ['power.bat']])

if __name__ == '__main__':

    runbatch(['Power_Spectra', ['power.bat']])
