# $Id: spiderOptions.py,v 1.1 2012/07/03 14:21:59 leith Exp $
#
# presents a multi-paned panel of options to the user

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
from   Tkinter import *
import Pmw
import GB, GG
from   spiderUtils import *
from   spiderGUtils import *
import spiderConfig
import spiderDButils
import spiderDialog
import spiderFonts
import spiderPrefs
import spiderSysprefs
import spiderInspect
import spiderExtapps

import types

def printChildren(d, level):
    keys = d.keys()
    for k in keys:
        dd = d[k].__dict__
        if dd.has_key('widgetName'):
            print level + "%s" % (dd['widgetName'])
        #print level + "%s: %s" % (k, str(d[k].__dict__))
        if d[k].__dict__.has_key('children'):
            printChildren(d[k].__dict__['children'],level+level)

#def printWindows():
    #keys = GG.topwindow.__dict__.keys()
    #for k in keys:
        #print "%s: %s" % (k,str(GG.topwindow.__dict__[k]))
    #print "------ children -------"
    #printChildren(GG.topwindow.children, " ")

    #print str(kids)
    #keys = kids.keys()
    #for k in keys:
        #print kids[k].__dict__


class optionNotebook:
    def __call__(self, page=""):
        self.__init__()
    def __init__(self, page=""):
        if not hasProject():
            displayError('Please open a project')
            return
        w = newWindow("Options")
        if not w: return
        w.protocol("WM_DELETE_WINDOW", self.quit)
        w.configure(background=GG.bgd03)
        self.win = w
        self.notebook = Pmw.NoteBook(w)
        self.applyFlag = 0
        if GG.prefs.balloonHelp:
            self.balloon = GG.balloon

        self.makeUserPrefsPage()
        self.makeFontsPage()
        self.makeSystemPage()
        self.makeConfigurationPage()
        self.makeInspectPage()
        self.makeExtappsPage()

        self.notebook.setnaturalsize()
        self.notebook.pack(side='top', fill='both',expand=1, padx=10, pady=10)
        
        self.makeDatabasePage() # do after notebook has been packed

        # Button frame at bottom
        fb = Frame(w, background=GG.bgd01, relief=GG.frelief, borderwidth=GG.brdr)
        b = Button(fb, text="Done", command=self.quit)
        b.pack(side='right', padx=10, pady=10)
        fb.pack(side='bottom', anchor='s', fill='x', expand=1)

        if page != "":
            self.notebook.selectpage(page)


    #   ===========================
    def makeConfigurationPage(self):
        page = self.notebook.add('Configuration')

        # Create the "Config file" contents of the page.
        group = Pmw.Group(page, tag_text = 'Configuration file:')
        fconf = group.interior()
        
        fc = Frame(fconf)
        self.cfile = StringVar()
        if hasProject() and hasattr(GB.P,'config'):
            self.cfile.set(GB.P.config)
        else:
            self.cfile.set(GG.sysprefs.configFile)
        centry = Entry(fc, textvariable=self.cfile)
        seeEntry(centry)
        centry.pack(side='left', fill='x', expand=1, padx=5, pady=10)

        bc = Button(fc,text='Browse',command=self.getFilename)
        bc.pack(side='right', padx=5, pady=10)
        fc.pack(side='top', fill='both', expand=1)

        padx = 5

        fb = Frame(fconf)           
        b1 = Button(fb, text = 'Read',
                    command=self.readConfig)
        b1.pack(side='left', padx=padx, pady=10)
        if GG.prefs.balloonHelp:
            self.balloon.bind(b1,'Load Dialogs and Directories\nfrom configuration file')
            
        b2 = Button(fb, text = 'Save',
                    command=self.saveConfig)
        b2.pack(side='left', padx=padx, pady=10)
        if GG.prefs.balloonHelp:
            self.balloon.bind(b2,'Save current Dialogs and\nDirectories to configuration file')
            
        b3 = Button(fb, text = 'Save As',
                    command=self.saveAsConfig)
        b3.pack(side='left', padx=padx, pady=10)
        if GG.prefs.balloonHelp:
            self.balloon.bind(b3,'Save current Dialogs and\nDirectories to an XML file')

        b4 = Button(fb, text = 'Edit',
                    command=spiderConfig.mkNewConfig)
        b4.pack(side='left', padx=padx, pady=10)
        if GG.prefs.balloonHelp:
            self.balloon.bind(b4,'graphical configuration editor')

        b5 = Button(fb, text = 'View',
                    command=spiderConfig.viewConfig)
        b5.pack(side='left', padx=padx, pady=10)
        if GG.prefs.balloonHelp:
            self.balloon.bind(b5,'View XML file in browser')
  
        b6 = Button(fb, text = 'Text\nedit',
                    command=spiderConfig.editConfig)
        b6.pack(side='left', padx=padx, pady=10)
        if GG.prefs.balloonHelp:
            self.balloon.bind(b6,'Edit XML file in %s' % (GG.prefs.editor))
            
        fb.pack(side='top', fill='both', expand=1)
        fconf.pack(fill='both', expand=1)
        group.pack(fill = 'both', expand = 1, padx = 10, pady = 10)

        # Create the "Dialog" contents of the page.
        group = Pmw.Group(page, tag_text = 'Dialogs:')
        #group.component('tag').configure(background=GG.bgd01)
        fdiag = group.interior()
        fd = Frame(fdiag)

        self.dialogmenu = []
        if hasConfig():
            for d in GB.C.Dialogs['dialogList']:
                if d == '.':
                    self.dialogmenu.append(GB.project_dir_title)
                else:
                    self.dialogmenu.append(d)
        
        self.cb = Pmw.ComboBox(fd, scrolledlist_items=self.dialogmenu)
        self.cb.pack(side='left', fill='x', padx=10, pady=10)
        if len(self.dialogmenu) > 0:
            self.cb.selectitem(0)   #self.dialogmenu[0])
        b1 = Button(fd, text = 'Edit', command=self.editDialog)
        b1.pack(side='left', padx=10, pady=10)
        if GG.prefs.balloonHelp:
            self.balloon.bind(b1,'Edit the selected Dialog')
            
        b2 = Button(fd, text = 'New', command=self.newDialog)
        b2.pack(side='left', padx=10, pady=10)
        if GG.prefs.balloonHelp:
            self.balloon.bind(b2,'Create a new Dialog')
        
        fd.pack(side='top', fill='both', expand=1)
        fdiag.pack(fill='both', expand=1)
        group.pack(fill = 'both', expand = 1, padx = 10, pady = 10)

        # Create the "Directories" contents of the page.
        group = Pmw.Group(page, tag_text = 'Directories:')
        #group.component('tag').configure(background=GG.bgd01)
        fdir = group.interior()
        fd = Frame(fdir)
        b1 = Button(fd, text = 'View directories', command=treeview)
        b1.pack(side='left', padx=10, pady=15)
        if GG.prefs.balloonHelp:
            self.balloon.bind(b1,'Tree view of files')
        b2 = Button(fd, text = 'Read from disk',
                    command=spiderConfig.readDirsFromDisk)
        b2.pack(side='left', padx=10, pady=15)
        if GG.prefs.balloonHelp:
            self.balloon.bind(b2,'Create xml directory\nstructure by reading the disk')
        
        fd.pack(side='top', fill='both', expand=1)
        fdir.pack(fill='both', expand=1)
        group.pack(fill = 'both', expand = 1, padx = 10, pady = 10)
        
    #   ===================
    def makeInspectPage(self):
        page = self.notebook.add('Inspect')
        f1 = Frame(page)
        button = Button(f1, text='view project',
                        command=spiderInspect.inspectProject)
        button.grid(row=0,column=0, padx=10,pady=10)
        button = Button(f1, text='view GB',
                        command=lambda g=GB: spiderInspect.inspectObject(g))
        button.grid(row=0,column=1, padx=10,pady=10)
        button = Button(f1, text='view preferences',
                        command=lambda g=GG.prefs: spiderInspect.inspectObject(g))
        button.grid(row=0,column=2, padx=10,pady=10)
        button = Button(f1, text='project file',
                        command=spiderInspect.inspectProjectFile)
        button.grid(row=1,column=0, padx=10,pady=10)
        f1.pack(side='top', fill='both', expand=1)
        f2 = Frame(page)
        self.object = StringVar()
        e = Entry(f2, textvariable= self.object)
        e.pack(side='left',fill='x',padx=10,pady=10)
        e.bind('<Return>', self.viewObject)
        b = Button(f2, text="View it", command=self.viewObject)
        b.pack(side='left',padx=10,pady=10)
        f2.pack(side='top', fill='both', expand=1)

    def viewObject(self, event=None):
        obj = self.object.get()
        spiderInspect.inspectObject(eval(obj))
        
    #   ======================
    def makeFontsPage(self):
        page = self.notebook.add('Fonts')
        group = Pmw.Group(page, tag_text = 'Fonts')
        fw = spiderFonts.FontWindow(group.interior())
        group.pack(fill = 'both', expand = 1, padx = 10, pady = 10)
       
    #   ======================
    def makeUserPrefsPage(self):
        page = self.notebook.add('Preferences')
        self.userPrefs = spiderPrefs.UserPreferences(page)
       
    #   ======================
    def makeSystemPage(self):
        page = self.notebook.add('System')
        self.sysPrefs = spiderSysprefs.SystemPreferences(page)
       
    #   ======================
    def makeExtappsPage(self):
        page = self.notebook.add('Applications')
        self.extApps = spiderExtapps.ExtApplications(page)
       
    #   ======================
    def makeDatabasePage(self):
        page = self.notebook.add('Database')
        #try:
        self.Database = spiderDButils.DatabaseWindow(page)
        #except:
            #pass

    #   ======================
    def applyFunc(self):
        #GG.prefs.balloonHelp = self.userPrefs.useBalloonVar.get()
        #GG.prefs.useDatabase = self.userPrefs.useDatabaseVar.get()
        #GG.prefs.saveResults = self.userPrefs.saveResultsVar.get()
        #GG.prefs.MaxResultLines = int(self.userPrefs.resEntry.get())
        #GG.prefs.MaxDisplayFiles = int(self.userPrefs.dirEntry.get())
        #GG.prefs.editor = self.userPrefs.edit.get()
        self.userPrefs.save()
        self.applyFlag = 1
        #showUserPrefs()
        
    # ===============================================
    # helper functions for the Config page

    def updateListbox(self):
        if hasConfig():
            self.dialogmenu = GB.C.Dialogs['dialogList']
            self.cb.component('listbox').delete(0,END)
            self.cb.clear()
            for item in self.dialogmenu:
                self.cb.component('listbox').insert(END, item)
            self.cb.selectitem(0)

    def getFilename(self):
        getFile(self.cfile,"*.xml")
        self.readConfig()

    def readConfig(self):
        file = self.cfile.get()
        config = spiderConfig.readXMLConfig(file)
        if config:
            GB.C = config
            GG.sysprefs.configFile = file
            self.updateListbox()

    def saveConfig(self):
        filename = self.cfile.get()
        if hasConfig():
            GB.C.save2xml(filename)
        else:
            spiderConfig.saveXMLConfig(filename)

    def saveAsConfig(self):
        file = askSaveAsFilename("*.xml")
        if file == "":
            return
        GG.sysprefs.configFile = file
        self.cfile.set(file)
        self.saveConfig()
        #spiderConfig.saveXMLConfig(file)

    def newDialog(self):
        spiderDialog.editDialog()
        self.updateListbox()

    def editDialog(self):
        dialog = self.cb.get()
        if dialog == GB.project_dir_title:
            dialog = '.'
        spiderDialog.editDialog(dialog)

    def quit(self):
        if not self.applyFlag:
            self.applyFunc()
        self.win.destroy()


    
