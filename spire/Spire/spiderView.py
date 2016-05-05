# $Id: spiderView.py,v 1.1 2012/07/03 14:21:59 leith Exp $
#
# Creates tables of project and data files

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
import GB,GG
from spiderUtils import *
from spiderGUtils import *
import spiderAddbatch
import spiderInspect
import spiderFtypes
from spiderClasses import SpiderBatchRun

def projView():
    if not hasProject():
        displayError("Please open a project")
        return
    try:
        os.chdir(GB.P.projdir)
    except:
        print "unable to change to project directory"
    GB.projview = projectViewer()


#########################################################################
#

class projectViewer:
    def __init__(self):
        w = newWindow("Project Viewer")
        if w == 0: return
        self.top = w
        # some attributes for this thing
        self.maxwidth = 24
        self.currentBatchButton = ""
        self.selectedBatchButton = ""   # selected buttons have selectColor
        self.currentOutputFile = ""
        self.selectedOutputButton = ""
        self.batchButtons = {}  # button dictionary, index = batch id
        self.outputButtons = {}  # button dictionary, index = filename
        self.font  = ('Courier', 11, 'normal')
        self.bfont = ('Courier', 11, 'bold')
        self.BatchButtonColor = 'white'
        self.OutputButtonColor = GG.sysbgd
        self.selectColor = '#ffff88'
        self.MaxDisplayFiles = GG.prefs.MaxDisplayFiles
        self.batBalloontxt = 'Left mouse button displays output files.\n'
        self.batBalloontxt += 'Right mouse button shows menu.'
        self.outBalloontxt = 'Left mouse button shows file in editor or Jweb.\n'
        self.outBalloontxt += 'Right mouse button shows menu.'
        if GG.prefs.balloonHelp:
            self.balloon = Pmw.Balloon(self.top)
            self.balloon.component('label').configure(font=GG.spid.font['small'])
        else:
            self.balloon = 0
        # variables for checkbuttons in menus
        self.askdelete = IntVar() ; self.askdelete.set(1)
        self.showballoon = IntVar() ; self.showballoon.set(1)

        # get the Project data
        P = {}   # a dictionary[id] = [batdir, batfile, date, time, fnums]
        self.batchkeys = GB.P.T.keys()
        self.batchkeys.sort()
        for k in self.batchkeys:
            br = GB.P.T[k]
            P[k] = [br.dir, br.batfile, br.time_start[0], br.time_start[1], br.filenumbers]
        
        self.createMenus()

        self.panedWidget = Pmw.PanedWidget(self.top, orient='vertical')

        # the top pane holds the batch runs
        self.headers = ['ID', 'Directory', 'Procedure', 'Date', 'Time', 'File numbers']
        self.hdrtxt = ""
        for h in self.headers:
            self.hdrtxt = h.center(12)

        self.batchPane = self.panedWidget.add('Batch runs')
        # outer frame holds headers and inner scrolled frame (bsf)
        self.obsframe = Frame(self.batchPane)
        self.headerButton = Button(self.obsframe, text=self.hdrtxt, font=self.bfont)
        self.headerButton.pack(side='top')
        # inner scrolled frame
        self.bsf= Pmw.ScrolledFrame(self.obsframe, hscrollmode='none')
        self.bframe = self.bsf.interior()

        self.fillBatchPane(P)
        self.bsf.pack(fill = 'both', expand = 1)
        self.obsframe.pack(fill = 'both', expand = 1)

        # the bottom pane holds the output files
        self.outputPane = self.panedWidget.add('Output files')

        self.psf= Pmw.ScrolledFrame(self.outputPane, labelpos='nw',
                                    label_text='Output files')

        self.psf.component('label').configure(font=self.bfont)
        self.pframe = self.psf.interior()
        # put a temporary button so bottom pane appears when requesting setnaturalsize
        btmp = Button(self.pframe, text = "select a batch run to view its output files",
                      relief='flat', font=self.font)
        btmp.pack(side='top', anchor='w', fill='x')
        self.outputButtons['tmp'] = btmp
        self.psf.pack(fill = 'both', expand = 1, padx=2, pady=2)

        self.panedWidget.pack(fill='both', expand=1)

        #self.top.update_idletasks()
        self.panedWidget.setnaturalsize()

        # end init --------------------------------------------------------

    def addNewBatchRun(self):
        " user can add files from disk "
        br = spiderAddbatch.addNewBatchRun()
        if br:
            saveBatchRun(br)

    def addBatchRun(self, br):
        " the project window must be open "
        if hasattr(self, 'top') and self.top.winfo_exists():
            b = (br.id, br.dir, br.batfile, br.time_start[0],
                 br.time_start[1], br.filenumbers)
            self.addBatchButton(b)
            self.seeProjectTable()

    def delBatchRun(self):
        id = self.currentBatchButton
        if GG.prefs.delAsk == 1 and self.askdelete.get():
            txt = 'This will delete this procedure run from the project.\n'
            txt = txt + 'Delete this line?'
            if not askOKorCancel(txt, parent=self.top): 
                return
        # delete the button from the table
        self.delBatchButton(id)
        # remove it from the project database
        deleteBatchRun(id)
        self.selectedBatchButton = ""

    def batchDetails(self):
        id = self.currentBatchButton
        br = GB.P.T[id]
        spiderInspect.inspectObject(br)

    def outputDetails(self):
        filename = self.currentOutputFile
        print filename

    def seeProjectTable(self, move='end'):
        y = 1.0
        if move == 'start': y = 0.0
        self.bsf.yview(mode='moveto', value=y)

    def getWidths(self, data, widths=None):
        " get the max widths of strings in a list or dictionary "

        W = [] # list of widths
        if widths != None:
            W = widths
        if len(data) == 0:
            return W

        if type(data) == type(['list']):
            item = data[0]
            n = len(item)
            if widths == None:
                for i in range(n):
                    W.append(0)
                
            for line in data:
                for i in range(n):
                    item = line[i]
                    x = len(item)
                    if x > W[i] and x < self.maxwidth:
                        W[i] = x 
        else:                          # assume it's a dictionary
            keys = data.keys()
            item = data[keys[0]]  # get the first item
            n = len(item)

            if widths == None:
                for i in range(n+1):
                    W.append(0)
            for k in keys:
                br = data[k]
                id = len(k)
                if id > W[0]: W[0] = id
                
                for i in range(n):
                    x = len(br[i])
                    if x > W[i+1]:
                        if x <= self.maxwidth: W[i+1] = x
                        else: W[i+1] = self.maxwidth
        return W

    def delBatchButton(self, id):
        " remove batch button from the table and internal dictionary"
        if id in self.batchButtons:
            b = self.batchButtons[id]
            b.pack_forget()
            del(self.batchButtons[id])
            self.top.update_idletasks()

    def addBatchButton(self, br):
        " br = [id, dir, batfile, date, time, filenums] "
        space = "  "
        id = br[0]
        batdir = br[1]
        s = id.ljust(self.batchWidths[0])
        i = 1
        for item in br[1:]:
            if len(item) > self.maxwidth:
                item = item[:self.maxwidth-3] + '...'
            s += space + item.ljust(self.batchWidths[i])
            i += 1

        b = Button(self.bframe, text=s, #relief='flat',
                   font = self.bfont, background=self.BatchButtonColor,
                   command=lambda k=id: self.fillOutputPane(k))
        b.pack(side='top', anchor='w') #, fill='x', expand=1)
        b.batdir = batdir  

        b.bind('<Button-3>', lambda event, k=id : self.batpopup(event,k))
        if self.balloon and self.showballoon.get():
            self.balloon.bind(b,self.batBalloontxt)

        self.batchButtons[id] = b
        
    def fillBatchPane(self, data):
        W = []
        for h in self.headers:
            W.append(len(h))
    
        widths = self.getWidths(data, widths=W)
        space = "  "
        self.batchWidths = widths
        for key in self.batchkeys:
            br = [key] + data[key]
            self.addBatchButton(br)

        # the headers at the top
        id = self.headers[0]
        hs = id.center(widths[0])
        i = 1
        for h in self.headers[1:]:
            hs += space + h.center(widths[i])
            i += 1
        self.headerButton.configure(text=hs)

    def fillOutputPane(self, id):
        # deselect previous selection, and make this button the selected color
        if self.selectedBatchButton:
            b = self.batchButtons[self.selectedBatchButton]
            b.configure(background=self.BatchButtonColor)
        b = self.batchButtons[id]
        b.configure(background=self.selectColor)
        self.selectedBatchButton = id
        
        # get output files
        batrun = getBatchRun(id, outputs=1)
        if hasattr(batrun, 'outfiles'):
            outfiles = batrun.outfiles[0] + batrun.outfiles[1] # doclist + binlist
        else:
            outfiles = []

        # check the number of output files
        noutfiles = len(outfiles)
        limit = noutfiles
        if noutfiles > self.MaxDisplayFiles:
            todo = self.tooManyFiles(noutfiles)
            if todo == 'few':
                limit = self.MaxDisplayFiles
            elif todo == 'all':
                limit = noutfiles
            else:
                return

        # remove the old buttons
        keys = self.outputButtons.keys()
        for k in keys:
            button = self.outputButtons[k]
            button.pack_forget()
            del(button)
        self.outputButtons = {}

        if noutfiles == 0:
            s = "no outputs to display"
            b = Button(self.pframe, text=s, relief='flat', font=self.font)
            b.pack(side='top', anchor='w')
            self.outputButtons['tmp'] = b
            return
        
        self.psf.configure(label_text="Output files for %s: %s" % (id, batrun.batfile))

        # get data from the outfile lists
        B = []  # list of [file, type, size, date, time]
        for f in outfiles[:limit]:
            fsize = f[2]
            size = fsize[0]
            for item in fsize[1:]:
                size += ',' + item
            
            #if f[1] == 'Document':
            #   size = f[2][0]
            #else:
            #   size = "%s,%s" % (f[2][0],f[2][1])
            B.append([f[0], f[1], size, f[3], f[4]])    
        widths = self.getWidths(B)

        # create the buttons
        space = "  "
        for line in B:
            filename = line[0]
            s = filename.ljust(widths[0])

            i = 1
            for item in line[1:]:
                if len(item) > self.maxwidth:
                    item = item[:self.maxwidth-3] + '...'
                s += space + item.rjust(widths[i])
                i += 1

            b = Button(self.pframe, text=s, relief='flat',
                       font=self.font,
                       command=lambda f=filename : self.viewOutput(f))
            b.pack(side='top', anchor='w')
            b.bind('<Button-3>', lambda event, k=filename : self.outpopup(event,k))
            if self.balloon and self.showballoon.get():
                self.balloon.bind(b,self.outBalloontxt)

            self.outputButtons[filename] = b

    def tooManyFiles(self, nfiles):
        var = IntVar()
        var.set(0)
        w = newWindow("That's a lot of files!")
        f1 = Frame(w, background=GG.bgd01, relief=GG.frelief, borderwidth=GG.brdr)
        txt  = "There are %s files.\nDisplay just the first few?" % str(nfiles)
        lbl= Label(f1, text=txt, background=GG.bgd01, anchor=W, justify='left')
        lbl.pack(padx=5, pady=5)
        f1.pack(side='top', fill='both', expand=1)
        
        Radiobutton(w, text='Show a few', value=1,
                    variable=var).pack(anchor='w')
        Radiobutton(w, text='Show them all',
                    value=2, variable=var).pack(anchor='w')
        Radiobutton(w, text='Cancel', value=3,
                    variable=var).pack(anchor='w')

        f1.waitvar(var)
        w.destroy()
        res = ""
        i = var.get()
        if i == 1: res = 'few'
        elif i == 2: res = 'all'
        elif i == 3: res = 'cancel'
        return res

    def viewOutput(self, filename=None):
        if not filename:
            filename = self.currentOutputFile

        # deselect previous selection, and make this button the selected color
        if self.selectedOutputButton:
            self.selectedOutputButton.configure(background=self.OutputButtonColor)
        if filename in self.outputButtons:
            b = self.outputButtons[filename]
            b.configure(background=self.selectColor)
            self.selectedOutputButton = b
      
        # batch directory must be present in path (if not projdir)
        pathlist = filename.split(os.sep)
        b = self.batchButtons[self.selectedBatchButton]
        if b.batdir == os.path.basename(os.getcwd()):
            # then you're in top-level directory
            pass
        elif b.batdir != pathlist[0]:
            filename = os.path.join(b.batdir, filename)
            
        viewFile(filename, verbose=0)

    def plotOutput(self, filename=None):
        if not filename:
            filename = self.currentOutputFile
        print "calling callPlotData(%s)" % filename
        callPlotData(filename)

    def maxFilesDisplay(self):
        pass

    def resetBalloon(self):
        if self.balloon and self.showballoon.get():
            keys = self.batchButtons.keys()
            for id in keys:
                b = self.batchButtons[id]
                self.balloon.bind(b,self.batBalloontxt)
            keys = self.outputButtons.keys()
            for k in keys:
                b = self.outputButtons[k]
                self.balloon.bind(b,self.outBalloontxt)
        else:
            keys = self.batchButtons.keys()
            for id in keys:
                b = self.batchButtons[id]
                self.balloon.unbind(b)
            keys = self.outputButtons.keys()
            for k in keys:
                b = self.outputButtons[k]
                self.balloon.unbind(b)

    def createMenus(self):
        self.brelief = 'flat'

        self.mBar = Frame(self.top, relief='raised', borderwidth=2)     
        self.makeOptMenu()
        #self.makeFileMenu()
        self.mBar.pack(side='top', fill='x')

        # create a popup menu for the batch pane
        self.batMenu = Menu(self.top, tearoff=0)
        self.batMenu.configure(font=GG.spid.font['small'])
        self.batMenu.add_command(label="details", command=self.batchDetails)
        self.batMenu.add_command(label="delete", command=self.delBatchRun)
        self.batMenu.bind("<Leave>", self.batunpopup)
        
        # create a popup menu for the output pane
        self.outMenu = Menu(self.top, tearoff=0)
        self.outMenu.configure(font=GG.spid.font['small'])
        self.outMenu.add_command(label="details", command=self.outputDetails)
        self.outMenu.add_command(label="view", command=self.viewOutput)
        #self.outMenu.add_command(label="plot", command=self.plotOutput)
        self.outMenu.bind("<Leave>", self.outunpopup)

    # current batch file, output file are set when popup menu is called
    def batpopup(self, event, id):
        " the -2 offset puts the cursor in the menu, cos <Leave> unposts"
        self.currentBatchButton = id
        self.batMenu.post(event.x_root-2, event.y_root-2)
    def batunpopup(self, event):
        self.batMenu.unpost()
    def outpopup(self, event, filename):
        self.currentOutputFile = filename
        self.outMenu.post(event.x_root-2, event.y_root-2)
    def outunpopup(self, event):
        self.outMenu.unpost()

    def makeOptMenu(self):
        Optbtn = Menubutton(self.mBar, text='Options', underline=0,
                                 relief=self.brelief)
        Optbtn.pack(side='left', padx=5, pady=5)
        Optbtn.menu = Menu(Optbtn, tearoff=0)

        Optbtn.menu.add_checkbutton(label='ask before delete', underline=0,
                                    variable=self.askdelete)
        Optbtn.menu.add_checkbutton(label='show popup help', underline=0,
                                    variable=self.showballoon,
                                    command=self.resetBalloon)
        #Optbtn.menu.add_command(label='max files display', underline=0,
        #                            command=self.maxFilesDisplay)
        Optbtn.menu.add_command(label='add batch run', underline=0,
                                command=self.addNewBatchRun)
        Optbtn.menu.add_separator()
        Optbtn.menu.add_command(label='done', underline=0,
                                     command=self.quit)
        Optbtn['menu'] = Optbtn.menu
        return Optbtn
    
    def makeFileMenu(self):
        File_button = Menubutton(self.mBar, text='Files', underline=0,
                                 relief=self.brelief)
        File_button.pack(side='left', padx=5, pady=5)
        File_button.menu = Menu(File_button, tearoff=0)

        File_button.menu.add_command(label='View', underline=0,
                                     command=self.dummy)
        File_button.menu.add_command(label='Edit', underline=0,
				     command=self.dummy)
        File_button.menu.add_command(label='Plot', underline=0,
                                     command=self.dummy)
        File_button['menu'] = File_button.menu
        return File_button

    def dummy(self):
        print "hi dummy"

    def quit(self):
        self.top.destroy()
        del(GB.projview)

