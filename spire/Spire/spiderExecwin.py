# $Id: spiderExecwin.py,v 1.1 2012/07/03 14:21:59 leith Exp $
#
# Displays a window to show an active Spider batch run.

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

import os
import Queue
import time, threading
import stat
from Tkinter import *

import GB, GG
from spiderUtils import *
from spiderGUtils import *
import spiderRemote
import spiderClasses

def mkExecWindow(execdir, cmd, batchrun):
    this_thread = threading.currentThread()
    if not hasattr(this_thread, 'package'):
        print "threadedGUIcall: no thread package found"
        return
    
    name = this_thread.package.name
    this_thread.package.func   = 'execWindow'
    this_thread.package.kwargs = {'execdir':execdir, 'cmd':cmd, 'br':batchrun}
    this_thread.package.module = 'spiderExecwin'
    
    e = threading.Event()
    this_thread.package.flag = e
    GB.ThreadDictionary[name] = this_thread.package
    
    GG.spidui.write_queue(name)  # request Main Gui to call function
    
    this_thread.waitevent = e  # in thread object, not package, for stopping
    e.wait()
    
    # check if e was set by requested function or by join()
    if this_thread._stopevent.isSet():
        return
    # else, get the package from the global dictionary & check output
    package = GB.ThreadDictionary[name]
    if hasattr(package, 'output'):
        result = package.output

    return result

##################################################################

def execBatchCleanup(ew=None, success=1):
    #print "execBatchCleanup"
    if ew != None:
        if hasattr(ew.br,'usingtmpfilenums') and ew.br.usingtmpfilenums != 0:
            #print "trying to delete %s" % ew.br.filenumfile
            delete(ew.br.filenumfile)
            ew.br.usingtmpfilenums = 0
        if not success:
            ew.quit()
            return   # leave the results file
        if not GG.prefs.saveResults:
            if os.path.exists(ew.br.resultfile):
                #print "trying to delete %s" % ew.br.resultfile
                delete(ew.br.resultfile)
        # remove remote shell files
        if hasattr(ew.br, 'script'):
            delete(ew.br.script)
        if hasattr(ew.br, 'spdout'):
            delete(ew.br.spdout)
        if hasattr(ew.br, 'spderr'):
            delete(ew.br.spderr)
        ew.quit()
##################################################################

class checkPIDthread(spiderClasses.threadObject):
    " had to be put in a thread when ExecWin was moved into Main thread "
    " call with execwin as argument "

    def run(self):
        if 'execwin' in self.kwargs:
            execwin = self.kwargs['execwin']
        else:
            return
    
        origpid = execwin.pid  
        oldpidlist = execwin.pidlist
        sleeptime = 1 # 1 second, check for 1st minute
        for i in range(60):
            if execwin.stop:
                break
            pidlist = spiderRemote.getSpiderPID(execwin.br.host)

            # if the old pid has disappeared..
            if origpid not in pidlist:
                # find the new one
                for np in pidlist:
                    if np not in oldpidlist:
                        execwin.insertpid(pid=np)
                        return
            time.sleep(sleeptime)            


cmd_color1 = '#77aa77'
cmd_color2 = '#99cc99'

class execWindow:
    """ window to show an ongoing spider process """
    def __call__(self, execdir, cmd, br):
        self.__init__(self, execdir, cmd, br)
    def __init__(self, execdir, cmd, br):
        self.br = br
        self.top = Toplevel(GG.topwindow)
        self.top.title("SPIDER process running")
        self.pid = ""
        self.stop = 0
        
        self.color1 = cmd_color1
        self.color2 = cmd_color2
                
        s = cmd.split()
        dispcmd = 'Running: spider ' + s[1] + " " + s[2]

        self.fr = Frame(self.top, background=GG.bgd01)

        self.cmdlabel = Label(self.fr, text=dispcmd, background=cmd_color1,
                        font=GG.spid.font['small'], relief=RIDGE, borderwidth=3)
        dirlabel = Label(self.fr, text="Dir: " + execdir, font=GG.spid.font['small'],
                         background=GG.bgd01)
        hstlabel = Label(self.fr, text="Host: " + GB.P.host,
                         font=GG.spid.font['small'],background=GG.bgd01)
        self.pidlabel = Label(self.fr, text="PID:  ", font=GG.spid.font['small'],
                         background=GG.bgd01)
        self.reslabel = Label(self.fr, text="Results file: ",
                         font=GG.spid.font['small'],background=GG.bgd01)
        self.cmdlabel.pack(side='top', padx=5, pady=2, anchor='w')
        dirlabel.pack(side='top', padx=5, pady=2, anchor='w')
        hstlabel.pack(side='top', padx=5, pady=2, anchor='w')
        self.pidlabel.pack(side='top', padx=5, pady=2, anchor='w')
        self.reslabel.pack(side='top', padx=5, pady=2, anchor='w')

        resbutton= Button(self.fr, text='results file',
                          command=self.showResults)      
        resbutton.pack(side='left', padx=5, pady=5)
        stopbutton= Button(self.fr, text='Kill', activebackground='red',
                            command=self.execExit)      
        stopbutton.pack(side='right', padx=5, pady=5)
        self.fr.pack()
        #self.top.update_idletasks()
        self.pidlabel.configure(text="PID: ")

        # start the blinker: 0 = no blink; 1 = use blink
        self.blink = 1
        
        # create a process queue to let threads request GUI calls
        self.queue = Queue.Queue()
        self.update_queue()
        
    def write_queue(self, thing):
        self.queue.put(thing)

    def update_queue(self):
        try:
            while 1:
                f = self.queue.get_nowait()
                if f is None:
                    pass
                else:
                    #print "   ExecwinQueue, next event: %s" % str(f)
                    if type(f) == type("string"):
                        eval(f)  
        except Queue.Empty:
            pass
        self.top.after(100, self.update_queue)
        
        # update blinker
        """
        if self.blink:
            self.blink += 100
            if self.blink > 1500:
                if hasattr(self, 'cmdlabel'):
                    self.cmdlabel.configure(background=self.color2)
                    self.top.update_idletasks()
            elif self.blink > 2000:
                if hasattr(self, 'cmdlabel'):
                    self.cmdlabel.configure(background=self.color1)
                    self.top.update_idletasks()
                self.blink = 1
        """

    def insertpid(self, pid, pidlist=None):
        " insertpid can be called by secondary threads "
        if pidlist == None: pidlist = []
        qstr = "self.insertpidQ(%s, %s)" % (str(pid), str(pidlist))
        #print qstr
        self.write_queue(qstr)

    def insertpidQ(self, pid, pidlist):
        self.pid = str(pid)
        self.pidlist = pidlist
        #print "insertpidQ: pid %s, pidlist %s" % (str(pid), str(pidlist))
        self.pidlabel.configure(text="PID: " + self.pid)
        self.top.update_idletasks()
        #self.top.after(500, self.checkpid)

    def checkpid(self):
        # sometimes the original pid (a script) exits and
        # starts a second Spider process (new pid)
        check_pid_thread = checkPIDthread(execwin=self)
        check_pid_thread.start()

    def insertres(self):
        self.write_queue("self.insertresQ()")
        
    def insertresQ(self):
        #print "execWin.insertres %s" % self.br.resultfile
        self.reslabel.configure(text="Results file: " + self.br.resultfile)
        self.top.update_idletasks()

    def filestat(self,filename):
        " returns a 2-tuple, (date-string, size) "
        if filename == "":
            return ("","")
        if not os.path.exists(filename):
            return ("","")
        st = os.stat(filename)
        tt = time.localtime(st[stat.ST_MTIME])
        time_str = time.asctime(tt)
        # asctime return format: 'Thu Oct 16 12:50:17 2003'
        size = st[stat.ST_SIZE]
        return time_str, size

    def showResults(self):
        results = self.br.resultfile
        if not os.path.exists(results):
            GB.errstream("Unable to find %s" % results)
            return
        print results
        """
        cmd = "ls -l %s" % (results)
        out =  getCommandOutput(cmd)
        res = out[0].split()
        if len(res) < 5:
            print "showResults: res= %s" % str(res)
            return
        size = res[4]
        try:
            i = int(size)
            rstr = "%s      updated %s %s %s,      size %s" % (res[-1],res[5],res[6],res[7],size)
        except:
            rstr = res
        """
        rftime, rfsize = self.filestat(results)
        if rftime == "":
            return
        rstr = "%s      updated %s,      size %s" % (results,rftime,rfsize)

        cmd = "tail -%d %s" % (GG.prefs.MaxResultLines, results)
        out =  getCommandOutput(cmd)
        output = out[0].split("\n")

        if not hasattr(self,'tw'):
            # first time called
            self.tw = textWindow(title=results, font='output', toptext=rstr)
        elif hasattr(self,'tw') and not self.tw.hasTextbox():
            # i.e., object exists but window has been killed
            self.tw = textWindow(title=results, font='output', toptext=rstr)
        elif self.tw.hasTextbox():
            self.tw.clear()
            self.tw.putToptext(rstr)
        else:
            return
        
        for line in output:
             self.tw.write(line)
        
    def execExit(self):      # called by the STOP button
        " assumes local "
        msg = "Stop the SPIDER process?\nAre you sure?"
        res = askYesorNo(msg, title="Kill SPIDER?")
        if not res:
            return
        host = self.br.host
        self.br.kill = 1
        self.stop = 1
        if self.pid.isdigit():
            killcmd = "kill -9 " + self.pid
            if GG.sysprefs.netexec != 'local':
                killcmd = "rsh %s '%s'" % (host, killcmd)
            #print killcmd
            os.system(killcmd)
            killtxt = "\nSpider process " + self.pid + " killed on " + host + ".\n"
            GB.outstream( killtxt, 'red')
        else:
            GB.outstream("Unable to kill process : no process ID")

        execBatchCleanup(self, success=0)

    def quit(self):
        " only quits the graphics part - doesn't remove class object "
        self.stop = 1
        if hasattr(self,'tw') or hasattr(self,'top'):
            self.write_queue("self.quitQ()")
        
    def quitQ(self):
        if hasattr(self,'tw'):
            self.tw.quit()
        if hasattr(self,'top'):
            self.top.update_idletasks()
            self.top.destroy()

# end execWindow
