# $Id: spiderMain.py,v 1.1 2012/07/03 14:21:59 leith Exp $
#
# Starts up the main SPIRE window

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

import os, re
import Queue, popen2
import string, shelve, sys
import time, threading
from commands import getoutput

from   Tkinter import *
import Pmw

import GB
import GG
import spiderBatch
import spiderBatform
import spiderClasses
import spiderConfig
from spiderDialog import makeDialogWindow
from spiderExecwin import execWindow
from spiderFilenums import readFileNumbers, FileNumbersButton, getFileNumbersEntry
import spiderProj
import spiderProj2html
import spiderParam
from   spiderUtils import *
from   spiderGUtils import *
import spiderOptions
import spiderView
import spiderSequence
import spiderIcons
from spiderReplace import vboffdialog

def threadedGUIexec(threadname):
    tpkg = GB.ThreadDictionary[threadname]
    func = tpkg.func
    # is the function visible in this scope?
    globs = globals().keys()
    if func not in globs:
        print "threadedGUIexec: function %s not found" % func
        if hasattr(tpkg, 'module'):
            module = tpkg.module
            if module in globs:
                func = module + "." + func
            else:
                # try importing the module.func?
                print "threadedGUIexec: module %s not found" % module
                return
        else:
            print "threadedGUIexec: function not in globs, package has no module"
            return
    kwargs = tpkg.kwargs
    
    result = apply(eval(func), (), kwargs)  # call the function 
    
    tpkg.output = result
    if hasattr(tpkg, 'flag'):
        tpkg.flag.set()

    if 0: #1:
        print "threadedGUIexec:"
        print "       %s" % str(tpkg.name)
        print "       %s" % str(tpkg.func)
        print "       %s" % str(tpkg.kwargs)
        print " "
     
def about():
    w = newWindow('About SPIRE')
    if w == 0: return
    appname = "%s Version %s\n\n" % (GG.applicationname, GG.applicationversion)
    copyright = 'Copyright 2006, 2010 Health Research Inc.,\nAlbany, NY.'
    copyright = copyright + ' All rights reserved.'
    Label(w, text=appname + copyright).pack(side='top', padx=10, pady=10)
    Button(w, text='Ok', command=w.destroy).pack(side='top', padx=10, pady=10)
    
def printChildren(widget):
    print "dict"
    wstr = "%s.__dict__" % (widget)
    print GG.topwindow.__dict__
    print "end dict"
    kids = GG.topwindow.children
    print str(kids)
    keys = kids.keys()
    for k in keys:
        print kids[k].__dict__


def runPopen3(cmd):
    child = popen2.Popen3(cmd, 1)
    return child
    
            

######################################################################
#
class SpiderGUI:

    def __init__(self, master, project=0, usesmallfont=0):

        self.threadname = threading.currentThread().getName()
        self.top = master
        self.top.iconname('SPIRE')
        self.usesmallfont = usesmallfont
        self.setup()

        self.icon = Toplevel(self.top)
        Label(self.icon, image=GG.icon).pack()
        self.top.iconwindow(self.icon)

        if GG.prefs.balloonHelp: self.balloon = GG.balloon
        else: self.balloon = 0
        
        self.setOptionDB(GG.topwindow)
        
        appname = "%s V%s" % (GG.applicationname, GG.applicationversion)
        self.top.title(appname)
        self.createMsgbox(self.top)  # make the output box first
        self.createMenus(self.top)
        self.createHeader(self.top)
        self.createFileNumbers(self.top)
        # pack output box here
        self.msgbox.pack(side='left', padx=5, pady=5, fill='both', expand=1) 
        self.msgfr.pack(side='top', fill='both', expand=1)

        master.protocol("WM_DELETE_WINDOW", self.quickGUIexit)
        self.top.update_idletasks()
        
        # create a process queue to let threads request GUI calls
        self.queue = Queue.Queue()
        self.update_queue()
        
        #if project:
        #   self.openProject(project)

    def setup(self):
        if self.usesmallfont:
            GG.prefs.font.setsmallfont()
            GG.padx=3
            GG.pady=3
        self.readUserPrefs()
        GG.icon = PhotoImage(data = spiderIcons.spider) #file = iconimage)
        # set up output streams for GUI
        self.msgfr = Frame(GG.topwindow,
                           relief=GG.frelief,
                           borderwidth=GG.brdr,
                           background=GG.bgd01)
        self.msgbox = Pmw.ScrolledText(self.msgfr, borderframe=4,
                                       vscrollmode='static',
                                       hscrollmode='dynamic',
                                       text_wrap='none')

        logfile = GG.sysprefs.logfile
        GB.outstream = GG.GUIOutput(self.msgbox, logfile)
        GB.errstream = GG.GUIOutput(self.msgbox, logfile)
        if GG.prefs.savelogfile:
            GB.outstream.uselogfile = 1
            GB.errstream.uselogfile = 1

        GG.balloon = Pmw.Balloon(GG.topwindow)
        GG.balloon.component('label').configure(font=GG.spid.font['small'])

    def setOptionDB(self, widget=GG.topwindow):
        " the call to readUserPrefs must be made before this "
        GG.spid = GG.prefs.font
        GG.colors = GG.prefs.colors
        GG.sysbgd = GG.colors.background
        
        widget.option_add('*font', GG.spid.font['medium'])
        widget.option_add('*background', GG.colors.background)
        widget.option_add('*Entry*background', GG.colors.entrybgd)
        widget.option_add('*foreground', GG.colors.foreground)
        
    def createMenus(self, master): # master = toplevel window
        self.brelief = 'flat'

	# menu bar ----------------------------------------------
        self.mBar = Frame(master, relief=GG.frelief, borderwidth=GG.brdr,
                          background=GG.sysbgd)

        self.makeProjMenu(master)
        self.makeParmMenu(master)
        self.makeCommMenu(master)
        if hasConfig():
            self.makeDialogMenu(master)
            self.makeBatchMenu(master)
            self.makeSequenceMenu(master)
        self.makeHelpMenu()

        self.mBar.pack(side='top', fill='x')

    def makeProjMenu(self, master):
        # make menu button : "Project"
        Proj_button = Menubutton(self.mBar, text='Project', underline=0,
                                 relief=self.brelief)
        Proj_button.pack(side='left', padx=5, pady=5)
        Proj_button.menu = Menu(Proj_button, tearoff=0)

        Proj_button.menu.add_command(label='New', underline=0,
                                     command=spiderProj.projNew)
                                     #command=Command(spiderProj.projForm,'new'))
        Proj_button.menu.add_command(label='Open', underline=0,
				     command=spiderProj.projOpen)
        Proj_button.menu.add_command(label='Edit', underline=0,
                                     command=Command(spiderProj.projEdit))
        Proj_button.menu.add_command(label='Save', underline=0,
                                     command=spiderProj.goprojSave)
        Proj_button.menu.add_command(label='Save as html', underline=0,
                                     command=spiderProj2html.proj2html)
        #Proj_button.menu.add_command(label='Test', underline=0,
        #                             command=self.testfunction)
        Proj_button.menu.add_command(label='Close', underline=0,
                                     command=self.closeProject)
        Proj_button.menu.add_separator()
        Proj_button.menu.add_command(label='Quit', underline=0,
                                     command=self.GUIexit)
        # set up a pointer from the file menubutton back to the file menu
        Proj_button['menu'] = Proj_button.menu
        return Proj_button

    def testfunction(self):
        showUserPrefs()

    def makeParmMenu(self, master):
        Parm_button = Menubutton(self.mBar, text='Parameters', underline=0,
                                 relief= self.brelief)
        Parm_button.pack(side='left', padx=5, pady=5)
        Parm_button.menu = Menu(Parm_button, tearoff=0)

        Parm_button.menu.add_command(label='New', underline=0,
                                     command=spiderParam.parmNew)
        Parm_button.menu.add_command(label='Edit', underline=0,
                                     command=spiderParam.parmOpen)
        Parm_button.menu.add_command(label='Read file', underline=0,
                                     command=spiderParam.readParmFile)
        #Parm_button.menu.add_command(label='File numbers', underline=0,
        #                             command=  )

        Parm_button['menu'] = Parm_button.menu
        return Parm_button

    def makeCommMenu(self, master):
        Comm_button = Menubutton(self.mBar, text='Commands', underline=0,
                                 relief= self.brelief)
        Comm_button.pack(side='left', padx=5, pady=5)
        Comm_button.menu = Menu(Comm_button, tearoff=0)

        Comm_button.menu.add_command(label='View project', underline=0,
                                     command = spiderView.projView)
        Comm_button.menu.add_command(label='View files', underline=0,
                                     command=treeview)
        Comm_button.menu.add_command(label='Edit file', underline=0,
                                     command=viewFile)
        Comm_button.menu.add_command(label='Plot data', underline=0,
                                     command=callPlotData)
        Comm_button.menu.add_command(label='Close all windows', underline=0,
                                     command = self.killallchildren)
        Comm_button.menu.add_command(label='Raise all windows', underline=0,
                                     command = self.raisechildren)
        Comm_button.menu.add_command(label='Change dir', underline=0,
                                     command=askdirectory)
        #Comm_button.menu.add_command(label='Batch form', underline=0,
                                     #command=spiderBatform.getBatch)
        #Comm_button.menu.add_command(label='Run Batch', underline=0,
                                     #command=spiderBatform.getBatch)
        Comm_button.menu.add_command(label='Add Batch', underline=0,
                                     command=addBatch)
        Comm_button.menu.add_command(label='Open Jweb', underline=0,
                                     command=self.startJweb)
        Comm_button.menu.add_command(label='Configuration', underline=0,
                                     command=Command(spiderOptions.optionNotebook,'Configuration'))
        Comm_button.menu.add_command(label='Options', underline=0,
                                     command=spiderOptions.optionNotebook)

        Comm_button['menu'] = Comm_button.menu
        return Comm_button

    def deletePreviousMenu(self, menu_name):
        kids = self.mBar.children
        keys = kids.keys()
        for k in keys:
            kid = kids[k]
            if kid.__dict__['widgetName'] == 'menubutton':
                if kid.cget('text') == menu_name:
                    self.mBar.children[k].destroy()
                    break

    def makeDialogMenu(self, master=None):
        # delete previous Dialog menu, if present
        self.deletePreviousMenu('Dialogs')
            
        Proc_button = Menubutton(self.mBar, text='Dialogs', underline=0,
                                 relief= self.brelief)
        Proc_button.pack(side='left', padx=5, pady=5)
        Proc_button.menu = Menu(Proc_button, tearoff=0)

        for d in GB.C.Dialogs['dialogList']:
            dialog = GB.C.Dialogs[d]
            if len(dialog.cmdlist) == 0: #no procedures, don't create dialog
                continue
            if d == '.':
                d = GB.project_dir_title
            Proc_button.menu.add_command(label=d, underline=0,
                                     command=Command(makeDialogWindow,dialog))
        Proc_button['menu'] = Proc_button.menu
        return Proc_button
    
    def makeBatchMenu(self, master=None):
        # delete previous menu, if present
        self.deletePreviousMenu('Batch files')

        # then make the main button in the top menu bar
        Prog_button = Menubutton(self.mBar, text='Batch files', underline=0,
                                 relief= self.brelief)
        Prog_button.pack(side='left', padx=5, pady=5)
        Prog_button.menu = Menu(Prog_button, tearoff=0)
        self.PB = Prog_button
        # make the submenus
        dirlist = GB.M['dirlist']
        for d in dirlist:
            if len(GB.M[d]) == 0:  # no procedures
                continue
            progs1 = Menu(Prog_button.menu, tearoff=0)
            self.addProgToProgMenu(d, progs1)
            
        Prog_button['menu'] = Prog_button.menu
        return Prog_button

    def addProgToProgMenu(self, dir, progmenu):
        for batfile in GB.M[dir]:
            if dir == GB.project_dir_title:
                runarg = [ GB.P.projdir, batfile ]
                fullname = os.path.join(GB.P.projdir,batfile)
            else:
	        runarg = [ dir, [batfile] ]
                if hasProject():
                    fullname = os.path.join(GB.P.projdir,dir,batfile)
                else:
                    fullname = os.path.join(dir,batfile)
                
	    progmenu.doit = Menu(progmenu, tearoff=0)
	    progmenu.doit.add_command(label='Edit',
                                      command=Command(spiderBatform.getBatch,
                                                      fullname))
	    progmenu.doit.add_command(label='Run',
				command=Command(spiderBatch.runbatch,runarg))
	    progmenu.add_cascade(label=batfile,	menu=progmenu.doit)
	
        self.PB.menu.add_cascade(label=dir, menu=progmenu)

    def makeSequenceMenu(self, master=None):
        self.deletePreviousMenu('Sequences')
        Seq_button = Menubutton(self.mBar, text='Sequences', underline=0,
                                 relief= self.brelief)
        Seq_button.pack(side='left', padx=5, pady=5)
        Seq_button.menu = Menu(Seq_button, tearoff=0)

        Seq_button.menu.add_command(label='Create', underline=0,
                                     command=spiderSequence.create)
        Seq_button.menu.add_command(label='Edit', underline=0,
                                     command=spiderSequence.edit)
        Seq_button.menu.add_command(label='Run', underline=0,
                                     command=spiderSequence.runseq)
        Seq_button['menu'] = Seq_button.menu
        return Seq_button
   
    def makeHelpMenu(self):
        Help_button = Menubutton(self.mBar, text='Help', underline=0,
                                 relief= self.brelief)
        Help_button.pack(side='right', padx=5, pady=5)
        Help_button.menu = Menu(Help_button, tearoff=0)

        Help_button.menu.add_command(label='Project Help', underline=0,
                                     command=Command(self.callSpireHelp,'project') )

        Help_button.menu.add_command(label='Spire Help', underline=0,
                                     command=Command(self.callSpireHelp, 'spire') )

        Help_button.menu.add_command(label='About', underline=0,
                                     command=about)

        Help_button['menu'] = Help_button.menu
        return Help_button

    def createHeader(self,master):
        bgd = GG.bgd01
        self.fr_hdr = Frame(master)
        self.fr_img  = Frame(self.fr_hdr, relief=GG.frelief,
                             borderwidth=GG.brdr, background=bgd)
        if os.path.exists(GG.mainImage):
            self.img = PhotoImage(file=GG.mainImage)  #, palette=256)   #/256/256)
            self.imglabel = Label(self.fr_img, image=self.img)
            self.imglabel.pack(padx=10, pady=10, fill='both')
        else:
            print "cannot find " + GG.mainImage
        
        self.frlabel = Frame(self.fr_hdr, relief=GG.frelief,
                             borderwidth=GG.brdr, background=bgd)
        self.labeltxt = GG.bigLabeltxt
        self.bigLabel = Label(self.frlabel, text=self.labeltxt, background=bgd,
                           font= GG.spid.font['large'])
        self.projLabel = Label(self.frlabel, text='Project: ',background=bgd)
        self.dirLabel = Label(self.frlabel, text='Directory: ',background=bgd)
        self.bigLabel.pack(side='top', padx=20, pady=20)
        self.projLabel.pack(side='top', anchor='w', padx=20, pady=2)
        self.dirLabel.pack(side='top', anchor='w', padx=20, pady=2)
        
        self.fr_img.pack(side='left', fill='both')
        self.frlabel.pack(side='right', fill='both', expand=1)
        self.fr_hdr.pack(fill='x', expand=0)

    def putImage(self, imagefile):
        if not GG.setMainImage(imagefile):
            print "cannot find %s" % imagefile
            return
        imagefile = GG.mainImage
        self.img = PhotoImage(file=imagefile)  #, palette=256)   #/256/256)
        self.imglabel.configure(image=self.img)

    def createMsgbox(self, master):
        #self.msgfr = msgfr   #  msgbox and  frame created in self.setup
        #self.msgbox = msgbox

        self.msgbox.component('text').configure(font=GG.spid.font['output'])
        self.msgbox.component('text').tag_configure('red', foreground='red',
                                font = GG.spid.font['outbold'])
        self.msgbox.component('text').tag_configure('green', foreground='#009900',
                                font = GG.spid.font['outbold'])
        self.msgbox.component('text').configure(state='disabled')
        
    def createFileNumbers(self, master):
        # file numbers file can only be read after a project is opened

        frfilenums = Frame(self.top, relief=GG.frelief, borderwidth=GG.brdr,
                           background=GG.bgd01)
        #fnlabel = Label(frfilenums, text="File numbers:", background=GG.bgd01)
        #fnlabel.pack(side='left', padx=5, pady=5)
        fnbtn = Button(frfilenums, text="File numbers:", background=GG.bgd01,
                       command=FileNumbersButton)
        fnbtn.pack(side='left', padx=5, pady=5)
        GG.balloon.bind(fnbtn, "select file numbers")
        fnentry = Entry(frfilenums, width=24, textvariable=GG.disp_fnums)
        fnentry.bind('<Return>', lambda e : readFileNumbers(e))
        fnentry.pack(side='left', padx=5, pady=5)
        frfilenums.pack(side='bottom', fill='x', expand=0)

        self.FilenumbersEntry = fnentry
        if not GG.prefs.useFilenumsEntry:
            self.FilenumbersEntry.configure(state='disabled')

    def setFilenumbersEntry(self,state='enabled'):
        if state != 'disabled':
            state = 'normal'
        self.FilenumbersEntry.configure(state=state)

    def startJweb(self):
        GB.outstream("starting Jweb...")
        spiderImage.startJweb(verbose=0)

    def callSpireHelp(self, which='spire'):
        if which == 'spire':
            spiderHelp(url = GG.SpireHelpURL)
        elif which == 'project':
            spiderHelp(url = GG.sysprefs.helpURL)

    def readUserPrefs(self):
        readUserPrefs(verbose=0)

    # Queue manipulation commands
    def write_queue(self, thing):
        self.queue.put(thing)

    def update_queue(self):
        # queue items may be strings or lists
        # strings: first check if it's a name in the thread dictionary
        #          else simply evaluate it: e.g., "showerror('Stop that!')"
        # lists: [ function, args ] where function can be a string or function
        #                           and args is a tuple
        try:
            while 1:
                f = self.queue.get_nowait()
                if f is None:
                    pass
                else:
                    #print "Queue, next event: %s" % str(f)
                    if type(f) == type("string"):
                        if GB.ThreadDictionary.has_key(f):
                            threadedGUIexec(f)
                        else:
                            # f itself has all needed info
                            eval(f)  
                    elif type(f) == type("list"):
                        func = f[0]
                        args = f[1] 
                        if type(func) == type("string"):
                            func = eval(f[0]) 
                        if type(args) != type(('a','tuple')):
                            args = tuple(args)
                        apply(func, args)
        except Queue.Empty:
            pass
        self.top.after(100, self.update_queue)

    def openProject(self, project):
        spiderProj.projOpen(project)

    def closeProject(self):
        if not hasProject():
            return
        projSave()
        spiderConfig.saveConfig()
        GB.DB = ""  # closeDatabase()
        self.killallchildren()
        GB.outstream("Project %s closed." % (GB.P.title))
        delattr(GB,'P')

    def killallthreads(self):
        this_thread = threading.currentThread()
        threads = threading.enumerate()  # list of current active threads
        nt = len(threads)
        if nt > 1:
            print "There are %d active threads" % nt
            for t in threads:
                if t != this_thread:   # a thread can't join itself
                    print "killing thread %s" % str(t)
                    sys.stdout.flush()
                    t.join()
        
    def killallchildren(self):
        winlist = self.top.winfo_children()
        for win in winlist:
            if win.winfo_exists():
                if win.winfo_class() == 'Toplevel':
                    win.destroy()

    def raisechildren(self):
        self.top.lift()
        winlist = self.top.winfo_children()
        for win in winlist:
            if win.winfo_exists():
                win.lift()
            
    def GUIexit(self):
	if hasProject():
            GB.outstream("saving project...")
            projSave()
        self.killallthreads()
	self.top.quit()

    # When quit toplevel via window mgr
    def quickGUIexit(self):
        if hasProject():
            GB.outstream("saving project...")
            projSave(0)
        self.top.quit()

# end class SpiderGUI
#
#######################################################################
