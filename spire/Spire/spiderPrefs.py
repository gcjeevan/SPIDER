# $Id: spiderPrefs.py,v 1.1 2012/07/03 14:21:59 leith Exp $
#
# Page for user preferences (see GG.prefs)

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
from Tkinter import *
import Pmw
import tkFont
import string
import GG
from spiderGUtils import *

class UserPreferences:

    def __init__(self,master):
        self.master = master
        if GG.prefs.balloonHelp:
            self.balloon = Pmw.Balloon(self.master)
        else:
            self.balloon = 0
            
        #prefs = GG.prefs
        #sys = GG.sysprefs
        self.frame = Frame(master)

	# preferences drop-down menu: Create and pack the MenuBar.
	self.menuBar = self.makeMenuBar()
	self.menuBar.pack(side='top', anchor = 'nw', padx=6, pady=4)

	self.makeEntries() # creates and packs entries
	self.makeSession() # creates and packs
	self.makeButtons()
        self.frame.pack(side='top',fill='both',expand=1)

        # Finally, set all the values
        self.setValues()

    def makeMenuBar(self):
        # check buttons for various preferences
        self.useBalloonVar = IntVar()
        self.useDatabaseVar = IntVar()
        self.saveResultsVar = IntVar()
        self.delAskVar = IntVar()
        self.logfileVar = IntVar()
        self.priorVar  = IntVar()
        self.filenumVar  = IntVar()
        self.jwebVar = IntVar()

        if self.balloon:
            menuBar = Pmw.MenuBar(self.master, hull_relief = 'raised',
                                  hull_borderwidth = 1, balloon=self.balloon)
	else:
            menuBar = Pmw.MenuBar(self.master, hull_relief = 'raised',
                                  hull_borderwidth = 1, balloon=None)
            
	preferences_menu = 'Preferences menu'

	menuBar.addmenu(preferences_menu, 'Click here for a menu of user preferences',
                        background=GG.bgd01,
                        borderwidth=GG.brdr+4)
	#
	menuBar.addmenuitem(preferences_menu, 'checkbutton',
                            'Turn these pop-up messages on/off',
                            label = 'Balloon help',
                            variable=self.useBalloonVar)
    	menuBar.addmenuitem(preferences_menu, 'checkbutton',
                            "Use/Don't use project file as a database",
                            label = 'save output files to project file',
                            variable=self.useDatabaseVar)
    	menuBar.addmenuitem(preferences_menu, 'checkbutton',
                            'Always save the SPIDER results file',
                            label = 'save results file',
                            variable=self.saveResultsVar)
    	menuBar.addmenuitem(preferences_menu, 'checkbutton',
                            'Save the Spire log file, %s' % (GG.sysprefs.logfile),
                            label = 'save log file',
                            variable=self.logfileVar)
	menuBar.addmenuitem(preferences_menu, 'checkbutton',
                            'Delete files from project without confirmation',
                            label = 'ask before deleting',
                            variable=self.delAskVar)
	menuBar.addmenuitem(preferences_menu, 'checkbutton',
                            'Check the project for previous runs of the same batch file',
                            label = 'check for prior runs of same batch file',
                            variable=self.priorVar)
	menuBar.addmenuitem(preferences_menu, 'checkbutton',
                            'File numbers in display take precedence over doc file',
                            label = 'Use filenums entry',
                            variable=self.filenumVar)
   	menuBar.addmenuitem(preferences_menu, 'checkbutton',
                            'Start Jweb at startup',
                            label = 'Start Jweb at startup',
                            variable=self.jwebVar)
   	return menuBar

    def makeEntries(self):
        frame = self.frame
        self.maxResultVar = StringVar()
        self.maxDisplayVar = IntVar()
        #self.displayprogVar = StringVar()
        
        # entries for max results lines, dir size, etc.
        ewidth = 12
        etxt = 'no. of lines to show in results file'
        self.resEntry = Pmw.EntryField(frame, labelpos='e',label_text=etxt)
        self.resEntry.pack(side='top', anchor='w',padx=GG.padx, pady=GG.pady) 
        self.resEntry.component('entry').configure(width=ewidth)

        etxt = 'display program for images'
        self.dispEntry = Pmw.EntryField(frame, labelpos='e',label_text=etxt)
        self.dispEntry.pack(side='top', anchor='w',padx=GG.padx, pady=GG.pady) 
        self.dispEntry.component('entry').configure(width=ewidth)
  
        etxt = 'max. no. files to display'
        self.dirEntry = Pmw.EntryField(frame, labelpos='e',
                                  label_text=etxt,
                                  value = GG.prefs.MaxDisplayFiles)
        self.dirEntry.component('entry').configure(width=ewidth)
        self.dirEntry.pack(side='top', anchor='w',padx=GG.padx, pady=GG.pady)

        # drop-down menu for editor
        editors = GG.editorlist
        self.edit = Pmw.ComboBox(frame, label_text='editor',labelpos='e',
                                 dropdown=1,
                                 scrolledlist_items=editors)
        self.edit.pack(side='top', anchor='w',padx=GG.padx, pady=GG.pady)

    def makeSession(self):
        group = Pmw.Group(self.frame, tag_text='Execution environment: ')
        gr = group.interior()

        exlab = Label(gr, text="The local host is %s" % gethostname())
        exlab.pack(side='top', anchor='e', padx= 2, pady=4)

        self.host = Pmw.ComboBox(gr, label_text='Run SPIDER on ',
                                labelpos='w',
                                dropdown=1,
                                scrolledlist_items=GG.hostlist)
        self.host.pack(side='top', anchor='w',padx=GG.padx, pady=GG.pady)

        shells = GG.remotecmdlist
        self.rsh = Pmw.ComboBox(gr, label_text='remote connection command',
                                labelpos='w',
                                dropdown=1,
                                scrolledlist_items=shells)
        self.rsh.pack(side='top', anchor='w',padx=GG.padx, pady=GG.pady)
        gr.pack(side='top',fill='both', expand=1, padx=5, pady=5)
        group.pack(fill='both', expand=1)

    def makeButtons(self):
        fbut = Frame(self.frame)
        
        saveButton = Button(fbut,text='Save',command=self.save)
        saveButton.pack(side='left', padx=GG.padx, pady=GG.pady)
        if GG.prefs.balloonHelp:
            self.balloon.bind(saveButton,'Save values to %s' % GG.interface.file)
        resetButton = Button(fbut,text='Reset',command=self.reset)
        resetButton.pack(side='left', padx=GG.padx, pady=GG.pady)
        if GG.prefs.balloonHelp:
            self.balloon.bind(resetButton,'Reset to values in %s' % GG.interface.file)
        defButton = Button(fbut,text='Defaults',command=self.default)
        defButton.pack(side='left', padx=GG.padx, pady=GG.pady)
        if GG.prefs.balloonHelp:
            self.balloon.bind(defButton,'Reset to system defaults')
            
        fbut.pack(side='top',fill='x',expand=1)     

    def save(self):
        " copy values to GG.interface "
        prefs = GG.prefs
        prefs.balloonHelp = self.useBalloonVar.get()
        prefs.useDatabase = self.useDatabaseVar.get()
        prefs.saveResults = self.saveResultsVar.get()
        GG.interface.system.checkPrior = self.priorVar.get()
        prefs.MaxResultLines = int(self.resEntry.get())
        prefs.MaxDisplayFiles = int(self.dirEntry.get())
        prefs.delAsk = self.delAskVar.get()
        prefs.useFilenumsEntry = self.filenumVar.get()
        prefs.startupJweb = self.jwebVar.get()
        prefs.displayProgram = self.dispEntry.getvalue()

        # logfile : if changed, must update output streams
        new = self.logfileVar.get()
        if GG.prefs.savelogfile != new:
            GG.prefs.savelogfile = new
            if GG.prefs.savelogfile:
                GB.outstream.uselogfile = 1
                GB.errstream.uselogfile = 1
            else:
                GB.outstream.uselogfile = 0
                GB.errstream.uselogfile = 0

        # the Filenums Entry in the main window
        if prefs.useFilenumsEntry: state = 'enabled'
        else: state = 'disabled'
        GG.spidui.setFilenumbersEntry(state)
            
        # the drop-down menus
        editor = self.edit.get()
        prefs.editor = editor
        if editor not in GG.editorlist:
            GG.editorlist.append(editor)

        host = self.host.get()
        GB.P.host = host
        if host not in GG.hostlist:
            GG.hostlist.append(host)
            
        remotecmd = self.rsh.get()
        if remotecmd != "":
            GG.interface.system.remotecmd = remotecmd

        writeUserPrefs()
        GB.outstream('Preferences saved to ' + GG.interface.file)

    def setValues(self):
        " set widgets to display values from GG.interface "
        self.useBalloonVar.set(GG.prefs.balloonHelp)
        self.useDatabaseVar.set(GG.prefs.useDatabase)
        self.saveResultsVar.set(GG.prefs.saveResults)
        self.delAskVar.set(GG.prefs.delAsk)
        self.priorVar.set(GG.sysprefs.checkPrior)
        self.logfileVar.set(GG.prefs.savelogfile)
        self.filenumVar.set(GG.prefs.useFilenumsEntry)
        self.jwebVar.set(GG.prefs.startupJweb)
        # entries
        self.resEntry.setentry(GG.prefs.MaxResultLines)
        self.dirEntry.setentry(GG.prefs.MaxDisplayFiles)
        self.dispEntry.setvalue(GG.prefs.displayProgram)
        # drop-downs
        self.edit.selectitem(GG.prefs.editor)
        self.rsh.selectitem(GG.sysprefs.remotecmd)
        
        if hasProject():
            host = GB.P.host
            if host not in GG.hostlist:
                GG.hostlist.append(host)
        
    def reset(self):
        " reset GG.interface to values in ~.spire "
        readUserPrefs()
        self.setValues()

    def default(self):
        " reset GG.interface to system defaults "
        GG.interface = GG.SysInterface()  # new instance with defaults
        GG.prefs = GG.interface.user
        GG.sysprefs = GG.interface.system

        GG.spid = GG.prefs.font
        GG.colors = GG.prefs.colors
        GG.sysbgd = GG.colors.background
        GG.bgd01 = GG.colors.bgd01
        GG.bgd02 = GG.colors.bgd02
        GG.bgd03 = GG.colors.bgd03
        self.setValues()
