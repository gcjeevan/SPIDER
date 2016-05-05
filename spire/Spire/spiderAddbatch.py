# $Id: spiderAddbatch.py,v 1.1 2012/07/03 14:21:59 leith Exp $
#
# Functions for manually adding a new batch run instance to the project
#
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

import os, string
from Tkinter import *
import Pmw
import GB,GG
from spiderUtils import *
from spiderGUtils import *
import spiderFtypes
from spiderClasses import SpiderBatchRun

# ---- classes for adding a new batch run
    
class newBatchRun:
    def __init__(self):
        self.procedure = "noname.spi"
        self.directory = ""
        self.outputfiles = []
        self.date, self.time, self.id = nowisthetime()

class addBatchRunForm:
    def __init__(self, w, newbat):
        self.win = w
        self.newbat = newbat
        f1 = Frame(w, relief=GG.frelief, borderwidth=GG.brdr, background=GG.bgd01)
        txt = "Add a new batch run to the project"
        Label(f1,text=txt, background=GG.bgd01).pack(padx=4, pady=4)
        f1.pack(side='top', fill='x', expand=1)

        f2 = Frame(w, relief=GG.frelief, borderwidth=GG.brdr)
        p = 4

        # procedure name
        self.procVar = StringVar()
        self.procVar.set(newbat.procedure)
        lbproc = Label(f2, text="procedure name:")
        entproc = Entry(f2, textvariable=self.procVar)
        lbproc.grid(row=0, column=0, padx=p, pady=p, sticky='e')
        entproc.grid(row=0, column=1, padx=p, pady=p, sticky='ew')

        # output files
        self.outputs = StringVar()
        lbout = Button(f2, text='output files:', command=self.getoutputs)
        entout = Entry(f2, textvariable=self.outputs)
        lbout.grid(row=1, column=0, padx=p, pady=p, sticky='e')
        entout.grid(row=1, column=1, padx=p, pady=p, sticky='ew')

        # date, time
        self.dateVar = StringVar()
        self.dateVar.set(newbat.date)
        self.timeVar = StringVar()
        self.timeVar.set(newbat.time)
        lbdat = Label(f2, text="date:")
        entdat = Entry(f2, textvariable=self.dateVar)
        lbdat.grid(row=2, column=0, padx=p, pady=p, sticky='e')
        entdat.grid(row=2, column=1, padx=p, pady=p, sticky='ew')
        lbtim = Label(f2, text="time:")
        entim = Entry(f2, textvariable=self.timeVar)
        lbtim.grid(row=3, column=0, padx=p, pady=p, sticky='e')
        entim.grid(row=3, column=1, padx=p, pady=p, sticky='ew')

        f2.grid_columnconfigure(1, weight=1)  # let entries expand
        
        f2.pack(side='top', fill='both', expand=1)

        fb = Frame(w, relief=GG.frelief, borderwidth=GG.brdr, background=GG.bgd01)
        cancel = Button(fb, text='Cancel', command=self.cancel)
        cancel.pack(side='left', padx=p, pady=p)
        ok = Button(fb, text='OK', command=self.quit)
        ok.pack(side='right', padx=p, pady=p) 
        fb.pack(side='bottom', fill='x', expand=1)

    def getoutputs(self):
        files = getFiles(parent=self.win)
        if len(files) == 0: return
        nf = []
        for file in files:
            f = projFilename(file)
            if os.sep in f:      # find which project directory it's in
                pdir, pat = pathpop(f)   # split path into (head, remainder)
                if hasattr(GB,'M') and pdir in GB.M:
                    self.newbat.directory = pdir
                    f = pat
                else:
                    path, base = os.path.split(f)
                    self.newbat.directory = path
            else:
                # toplevel directory
                projdir = os.path.dirname(file)
                self.newbat.directory = projdir
                
            nf.append(f)

        # put list back into string of filenames (appears in entry box)
        fstr = ""
        for f in nf:
            fstr += f + ","
        fstr = fstr[:-1]
        self.outputs.set(fstr)

    def quit(self):
        self.newbat.procedure = self.procVar.get()
        outfiles = self.outputs.get()
        if outfiles.find(",") > 0:
            self.newbat.outputfiles = outfiles.split(",")
        else:
            self.newbat.outputfiles = [outfiles]
        self.newbat.date = self.dateVar.get()
        self.newbat.time = self.timeVar.get()
        self.win.destroy()

    def cancel(self):
        self.newbat.procedure = ""
        self.win.destroy()

# ==========================================================
def addNewBatchRun():
    " user can add files from disk "
    win = newWindow("Add new data to project")
    if win == 0: return ""
    nbr = newBatchRun() # create a new batch run object
    abr = addBatchRunForm(win, nbr)  # display the form
    win.wait_window(win)
    if nbr.procedure == "":  # cancel signal
        return ""
    # shorten top level dir
    if nbr.directory == GB.P.projdir:
        nbr.directory = os.path.basename(nbr.directory)
    # else create a new batch run object
    b = SpiderBatchRun()
    b.id      = nbr.id
    b.batfile = nbr.procedure
    b.dir     = nbr.directory
    datime  = ( nbr.date, nbr.time )
    b.time_start = datime
    b.time_end = datime
    b.projID = GB.P.ID
    # get info about the output files
    cwd = os.getcwd()
    if b.dir == os.path.basename(GB.P.projdir):
        newdir = GB.P.projdir
    else:
        newdir = os.path.join(GB.P.projdir,b.dir)
    chdir(newdir)
    doclist = []
    binlist = []
    print nbr.outputfiles
    for file in nbr.outputfiles:
        f = spiderFtypes.getFileType(file)
        print "%s:%s" % (file,str(f))
        type = f[1]
        if type == 'Document':
            doclist.append(f)
        else:
            binlist.append(f)
    b.outfiles = [doclist, binlist]
    chdir(cwd)
    return b

