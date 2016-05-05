# $Id: spiderExtapps.py,v 1.1 2012/07/03 14:21:59 leith Exp $
#
# Link file extensions to external applications (used on Options page)

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
import GG

class ExtApplications:

    def __init__(self,master):
        self.master = master
        if GG.prefs.balloonHelp:
            self.balloon = GG.balloon

        self.AppDict = GG.sysprefs.AppDict
            
        self.masterFrame = Frame(master)
        self.sf = Pmw.ScrolledFrame(self.masterFrame)
        self.frame = self.sf.interior()
        self.makeAppDisplay()
        self.sf.pack(side='top', fill='both', expand=1, padx=5, pady=5)
        self.addButtons()
        self.masterFrame.pack()

    def makeAppDisplay(self):
        fr = self.frame
        keys = self.AppDict.keys()
        keys.sort()

        row = 0
        self.textVarList = []

        for ext in keys:
            app = self.AppDict[ext]
            sv1 = StringVar()
            sv2 = StringVar()
            sv1.set(ext)
            sv2.set(app)
            e1 = Entry(fr, textvariable=sv1)
            e2 = Entry(fr, textvariable=sv2)
            self.textVarList.append( [sv1,sv2] )
            e1.grid(row=row, column=0)
            e2.grid(row=row, column=1)
            row += 1
            self.nrows = row

    def addButtons(self):
        fr = self.masterFrame
        bnew = Button(fr, text='New', command=self.new)
        bnew.pack(side='left', padx=4, pady=4)
        snew = Button(fr, text='Save', command=self.save)
        snew.pack(side='left', padx=4, pady=4)

    def new(self):
        " add a new blank pair of extension:application entries "
        sv1 = StringVar()
        sv2 = StringVar()
        e1 = Entry(self.frame, textvariable=sv1)
        e2 = Entry(self.frame, textvariable=sv2)
        self.textVarList.append( [sv1,sv2] )
        e1.grid(row=self.nrows, column=0)
        e2.grid(row=self.nrows, column=1)
        self.nrows += 1
        self.sf.yview(mode='moveto', value=1)

    def save(self):
        " put the new values in GG.sysprefs "
        newappdict = {}
        for item in self.textVarList:
            ext,app = item[0].get().strip(), item[1].get().strip()
            if ext != "" and app != "":
                # by default, extension strings have a leading '.'
                if ext[0] != '.':
                    ext = '.' + ext
                newappdict[ext] = app
                #print "%s : %s" % (ext,app)
        GG.sysprefs.AppDict = newappdict
