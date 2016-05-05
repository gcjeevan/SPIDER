# $Id: spiderSequence.py,v 1.1 2012/07/03 14:21:59 leith Exp $
#
# Create and run sequences of Spider batch files

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
from Tkinter import *
import Pmw

import GB, GG
import spiderBatch
from   spiderUtils import *
from   spiderGUtils import *

def create():
    batlist = []
    dirlist = GB.M['dirlist']
    for d in dirlist:
        blist = GB.M[d]
        if len(blist) == 0:  # no procedures
            continue
        for bat in blist:
            if d == GB.project_dir_title:
                batlist.append(bat)
            else:
                s = d + os.sep + bat
                batlist.append(s)

    sw = newWindow('Sequence editor')
    if sw != 0:
        seq = Sequence(sw, batchfiles=batlist)

def edit():
    create()

def runseq(filename=None):
    if filename == None or filename == "":
        filename = askfilename()
    if filename == "":
        return
    B = fileReadLines(filename)
    newlist = []
    for item in B:
        newlist.append(item.strip())
    runargs = []
    for item in newlist:
        path,base = os.path.split(item)
        if path == '':
            path = '.'
        arg = (path, [base])
        runargs.append(arg)

    if not GG.prefs.savelogfile: # turn on the log file for sequence
        GB.outstream.uselogfile = 1
        GB.errstream.uselogfile = 1
        
    spiderBatch.runbatch(runargs)

    if not GG.prefs.savelogfile: # turn off the log file if desired
        GB.outstream.uselogfile = 0
        GB.errstream.uselogfile = 0


    

#########################################################################
#
# Double listbox widget for creating sequences
#
# Left box
# ">>" or dbl_click: Add selected items from list on left to box on right
# Right box: dbl_click: remove from list
# Browse: add individual items to rightlist
# Load: add all items within a file to rightlist
# Save: save rightlist to a file
# Remove: Remove selected items from rightlist

class Sequence:
    def __init__(self, parent, batchfiles=None):
        self.top = parent
        if batchfiles != None:
            self.batchfiles = batchfiles
        ftop = Frame(parent, relief=GG.frelief, borderwidth=GG.brdr,
                     background=GG.bgd01)
        fmid = Frame(parent)
        fbot = Frame(parent, relief=GG.frelief, borderwidth=GG.brdr,
                     background=GG.bgd01)

        self.sequence_file = ""

        # top frame = Menubar?
        self.label = Label(ftop, text="Batch file sequence editor")
        self.label.pack()
        ftop.pack(side='top', fill='x', expand=0)

        # bottom frame with buttons
        loadb = Button(fbot, text='Load\nSeq.', command=self.load)
        saveb = Button(fbot, text='Save\nSeq.', command=self.save)
        runseqb = Button(fbot, text='Run\nSeq.', command=self.runseq)

        browseb = Button(fbot, text='Add\nBatch', command=self.browse)
        removeb = Button(fbot, text='Remove\nBatch', command=self.remove)
        clearb = Button(fbot, text='Clear', command=self.clearall)
        cancelb = Button(fbot, text='Done', command=self.cancel)
        px = py = 4
        loadb.pack(side='left', padx=px, pady=py)
        saveb.pack(side='left', padx=px, pady=py)
        runseqb.pack(side='left', padx=px, pady=py)
        
        cancelb.pack(side='right', padx=px, pady=py)
        clearb.pack(side='right', padx=px, pady=py)
        removeb.pack(side='right', padx=px, pady=py)
        browseb.pack(side='right', padx=px, pady=py)
        fbot.pack(side='bottom', fill='x', expand=0)

        # ----- middle frame with list boxes -----
        # Left frame with batch files
	self.leftbox = Pmw.ScrolledListBox(fmid,
		items=self.batchfiles,
		labelpos='nw',
		label_text='batch files',
		listbox_height = 6,
		#selectioncommand=self.selectionCommand,
		dblclickcommand=self.add
	)
	self.batchlistbox = self.leftbox.component('listbox')
	self.batchlistbox.configure(background='white')
	self.batchlistbox.configure(selectmode=EXTENDED)

	addbut = Button(fmid, text='>>', command=self.add)
        
        # right frame with selections
	self.seqbox = Pmw.ScrolledListBox(fmid,
		items=[],
		labelpos='nw',
		label_text='sequence',
		listbox_height = 6,
		#selectioncommand=self.selectionCommand,
		dblclickcommand=self.remove
	)
	self.seqlistbox = self.seqbox.component('listbox')
	self.seqlistbox.configure(background='white')
	self.seqlistbox.configure(selectmode=EXTENDED)
	# for drag'n'drop
        self.seqlistbox.bind('<Button-1>', self.setCurrent)
        self.seqlistbox.bind('<B1-Motion>', self.shiftSelection)
        self.seqlistbox.curIndex = None

	self.leftbox.pack(side='left', anchor='n', fill='both', expand=1)
	addbut.pack(side='left', padx=5, anchor='center')
	self.seqbox.pack(side='right', fill='both', expand=1)
	fmid.pack(side='top', fill='both', expand=1)

    # drag and drop functions
    def setCurrent(self, event):
        self.seqlistbox.curIndex = self.seqlistbox.nearest(event.y)

    def shiftSelection(self, event):
        rlb = self.seqlistbox
        rlb.select_clear(0,'end') # need to clear selections when dragging?
        i = rlb.nearest(event.y)
        if i < rlb.curIndex:
            x = rlb.get(i)
            rlb.delete(i)
            rlb.insert(i+1, x)
            rlb.curIndex = i
        elif i > rlb.curIndex:
            x = rlb.get(i)
            rlb.delete(i)
            rlb.insert(i-1, x)
            rlb.curIndex = i

    def add(self, items=None):
        if items != None:
            if type(items) == type("string"):
                sels = [items]
            elif type(items) == type(["list"]) or type(items) == type(("tuple",)):
                sels = items
            else:
                return
        else:
            sels = self.leftbox.getcurselection()
	if len(sels) == 0:
	    return
	else:
            for item in sels:
                self.seqbox.insert('end', item)
	    self.batchlistbox.select_clear(0,'end')

    def clearall(self):
        self.seqbox.clear()

    def runseq(self):
        self.top.destroy()
        if self.sequence_file:
            runseq(self.sequence_file)
        else:
            runseq()

    def browse(self):
        " add files to sequence box"
        filenames = getFiles()  # multiple selections allowed
        if len(filenames) == 0:
            return
        newfilenames = []
        for file in filenames:
            newfilenames.append(projFilename(file))
        self.add(items=newfilenames)
        
    def load(self):
        " read a sequence file "
        filename = askfilename()
        if filename == "":
            return
        B = fileReadLines(filename)
        new = []
        for item in B:
            new.append(item.strip())
        self.add(items=new)
        seqfile = os.path.basename(filename)
        self.label.configure(text=seqfile)
        self.sequence_file = filename
    
    def save(self):
        filename = askSaveAsFilename()
        if filename == "":
            return
        allitems = self.seqbox.get()
        itemlist = []
        for item in allitems:
            itemlist.append(item + "\n")
        fileWriteLines(filename, itemlist)
        seqfile = os.path.basename(filename)
        self.label.configure(text=seqfile)
        self.sequence_file = filename
    
    def remove(self):
        "delete selected items from list box on the right"
	sels = self.seqbox.getcurselection()
	if len(sels) == 0:
	    return
	else:
	    allitems = self.seqbox.get()
	    newlist = []
	    for item in allitems:
                if item not in sels:
                    newlist.append(item)
            self.seqbox.setlist(newlist)
        
    def cancel(self):
        self.top.destroy()

