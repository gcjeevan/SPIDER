# $Id: spiderSysprefs.py,v 1.1 2012/07/03 14:21:59 leith Exp $
#
# Handles system preferences (see GG.sysprefs)

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
import os,string
import GG
from spiderGUtils import *

class SystemPreferences:

    def __init__(self,master):
        self.master = master
        if GG.prefs.balloonHelp:
            self.balloon = GG.balloon
            
        self.frame = Frame(master)
	self.makeEntries()
	self.makeButtons()
        self.setValues()
        self.frame.pack()
	
    def makeEntries(self):
        prefs = GG.prefs
        sysprefs = GG.sysprefs
        ewidth = 24
        frame = self.frame

        etxt = 'threshold for checking large directories'
        self.maxdirEntry = Pmw.EntryField(frame, labelpos='e',
                                  label_text=etxt)
        self.maxdirEntry.pack(side='top', anchor='w', padx=GG.padx, pady=GG.pady) 
        self.maxdirEntry.component('entry').configure(width=ewidth)

        self.filenumEntry = Pmw.EntryField(frame, labelpos='e',
                                  label_text='file numbers file')
        self.filenumEntry.pack(side='top', anchor='w',padx=GG.padx, pady=GG.pady) 
        self.filenumEntry.component('entry').configure(width=ewidth)

        self.paramEntry = Pmw.EntryField(frame, labelpos='e',
                                  label_text='parameter file')
        self.paramEntry.pack(side='top', anchor='w',padx=GG.padx, pady=GG.pady) 
        self.paramEntry.component('entry').configure(width=ewidth)

        self.configEntry = Pmw.EntryField(frame, labelpos='e',
                                  label_text='configuration file')
        self.configEntry.pack(side='top', anchor='w',padx=GG.padx, pady=GG.pady) 
        self.configEntry.component('entry').configure(width=ewidth)

        ewidth = 36
        self.helpEntry = Pmw.EntryField(frame, labelpos='e',
                                  label_text='Help URL')
        self.helpEntry.pack(side='top', anchor='w',padx=GG.padx, pady=GG.pady) 
        self.helpEntry.component('entry').configure(width=ewidth)
 
        self.spiderEntry = Pmw.EntryField(frame, labelpos='e',
                                  label_text='spider command')
        self.spiderEntry.pack(side='top', anchor='w',padx=GG.padx, pady=GG.pady) 
        self.spiderEntry.component('entry').configure(width=ewidth)

        """
        self.labelEntry = Pmw.EntryField(frame, labelpos='e',
                                  label_text='Main label text')
        self.labelEntry.pack(side='top', anchor='w',padx=GG.padx, pady=GG.pady) 
        self.labelEntry.component('entry').configure(width=ewidth)
 
        self.imageEntry = Pmw.EntryField(frame, labelpos='e',
                                  label_text='image file')
        self.imageEntry.pack(side='top', anchor='w',padx=GG.padx, pady=GG.pady) 
        self.imageEntry.component('entry').configure(width=ewidth)
        """
        

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

    def setValues(self):
        prefs = GG.prefs
        sysprefs = GG.sysprefs
        self.entries = [self.maxdirEntry, self.filenumEntry, self.paramEntry,
                        self.configEntry, self.helpEntry, self.spiderEntry] #,
                        #self.labelEntry, self.imageEntry]
        self.maxdirEntry.setvalue(sysprefs.MaxDirsize)
        self.filenumEntry.setvalue(sysprefs.filenumFile)
        self.paramEntry.setvalue(sysprefs.paramFile)
        self.configEntry.setvalue(sysprefs.configFile)
        self.helpEntry.setvalue(sysprefs.helpURL)
        self.spiderEntry.setvalue(sysprefs.spider)
        #self.labelEntry.setvalue(prefs.bigLabeltxt)
        #self.imageEntry.setvalue(prefs.mainImg)
        for entry in self.entries:
            seeEntry(entry)

    def save(self):
        " copy values to GG.interface "
        prefs = GG.prefs
        sysprefs = GG.sysprefs

        sysprefs.filenumFile = self.filenumEntry.getvalue()
        sysprefs.paramFile = self.paramEntry.getvalue()
        
        sysprefs.MaxDirsize = string.strip(self.maxdirEntry.getvalue())
        sysprefs.configFile = self.configEntry.getvalue()
        sysprefs.helpURL = self.helpEntry.getvalue()
        sysprefs.spider = self.spiderEntry.getvalue()
        #prefs.bigLabeltxt = self.labelEntry.getvalue()
        #prefs.mainImg = self.imageEntry.getvalue()

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
