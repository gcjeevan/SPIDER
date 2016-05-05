# $Id: spiderClasses.py,v 1.1 2012/07/03 14:21:59 leith Exp $
#
# various classes used by Spire

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
#------------------------------------------------------------
"""
classes
   SpiderProject
   SpiderBatchRun
   SpiderDatabase
   Config
   saveConfig2xml
   scrolledForm

"""
import os
import shelve
import threading
from Tkinter import *
import Pmw

import GB,GG
import spiderGUtils
from spiderUtils import isMainThread, nowisthetime, gethostname

class SpiderProject:
    """ class for Spider projects """
    def __init__(self, **kwargs):
        """ set default values, decode keyword args """
        self.ID = ""
        self.title = ""
        self.name = ""  # short title
        self.projfile = "proj001"
        self.projdir = os.getcwd()
        self.dataext = "dat"
        self.host = gethostname()
        self.RunList = []   # a list of batchrun id's
        self.SpiderBatchDir = ""
        self.config = GG.sysprefs.configFile
        (date, time, x) = nowisthetime()
        self.startdate = "%s, %s" % (date, time)
        self.updated = ""
        self.parameters = {}
        self.pixelsize = ""
        self.kv = ""
        self.Cs = ""
        self.SpireVersion = GG.applicationversion
        
        keywords = ['ID', 'id', 'title','file','dir','projdir','config',
                    'dataext','ext','host','SpiderBatchDir', 'name']
        for kw in kwargs:
            if kw not in keywords:
                GG.errstream("%s not a valid keyword" % kw)
                return
            if kw == 'id' or kw == 'ID': self.ID = kwargs[kw]
            elif kw == 'title': self.title = kwargs[kw]
            elif kw == 'name': self.name = kwargs[kw]
            elif kw == 'file': self.projfile = kwargs[kw]
            elif kw == 'dir' or kw == 'projdir': self.projdir = kwargs[kw]
            elif kw == 'ext' or kw == 'dataext': self.name = kwargs[kw]
            elif kw == 'host': self.host = kwargs[kw]
            elif kw == 'config': self.host = kwargs[kw]
            elif kw == 'SpiderBatchDir': self.SpiderBatchDir = kwargs[kw]

####################################################################
class SpireoutParms:
    def __init__(self):
        self.runningline = "" # Running: /net/bali/usr1/spider/bin/spider5mp_tmp
        self.version = ""     # VERSION:  UNIX  12.04 ISSUED: 09/12/2005
        self.startdate = ""
        self.starttime = ""
        self.pid = ""
        self.enddate = "" # from COMPLETED  13-SEP-2005 at 05:00:17
        self.endtime = ""
        self.stopline = ""  # **** SPIDER NORMAL STOP ****

####################################################################
class SpiderBatchRun:
    def __init__(self):
        self.id = ""    # identifier
        self.pid = ""   # process ID
        self.batfile = ""
        self.dir  = ""
        self.dataext = ""
        self.host = ""
        self.time_start = ("","")  # tuple (date, time)
        self.time_end = ("","")    # e.g., ("21-SEP-2003", "03:44:15")
        self.projID = ""
        self.results = ""
        self.text = ""
        self.filenumbers = ""
        self.parameters = []
        self.outfiles = []
        self.delete = 0 # nonzero if any outfiles marked for deletion
        self.spiderversion = '0.0'
        self.spidercmd = "none"   # e.g. ['UNIX  11.7', 'spider5mp.255']
        # each file in outfiles consists of [name, type, size, date, time]
        # e.g. ['power/roo001.blp', 'Document', ('250', '11136'), '14-OCT-2003', '15:55:17']

####################################################################
# class for internal database, a shelve object
#
# database is closed between accesses
# external methods:
#   GB.DB = ProjectDatabase(filename)   # create instance
#   GB.DB.newDatabase(filename)   
#   GB.DB.put(key, object)   # key = 'Project'|'Config'
#   p = GB.DB.get(key)       # key = 'Project'|'Config'
#   b = GB.DB.BatchRun(id)
#   GB.DB.addBatchRun(batchrun, id=None)
#   GB.DB.delBatchRun(id)
#   runlist = GB.DB.RunList()
#  (open,closeDatabase should not be used except by class)

class ProjectDatabase:
    " Each method must access via self.openDatabase, self.closeDatabase "
    def __init__(self, filename, new=0, quiet=0):
        self.SpiderProjectDatabase = 1   # for type checking
        self.database = {}               # will later be a shelve object

        self.filename, xxt = os.path.splitext(filename)  # project file =no extension 
        self.lock = threading.Lock()
    
        if new:
            if self.openDatabase(new=1):
                if not quiet:
                    GB.outstream('Project file %s opened' % self.filename)
                self.closeDatabase()
            else:
                return None
            
        # else open pre-existing project file
        else:
            try:
                if self.openDatabase():
                    if not quiet:
                        GB.outstream('Project file %s opened' % self.filename)
                    self.closeDatabase()
            except:
                GB.errstream('Unable to open project file %s' % self.filename)
                return None
            
    def error(self, text):
        GB.errstream(text)

    def Keys(self):
        keys = []
        if self.openDatabase():
            keys = self.database.keys()
            self.closeDatabase()
        return keys

    def get(self, key='Project'):
        " key is either 'Project' or 'Config'. Returns the project/config object "
        if self.openDatabase():
            if self.database.has_key(key):
                p = self.database[key]
                self.closeDatabase()
                return p
            else:
                return None
        else:
            return None

    def put(self, key, object):
        " for putting Project, Config in database "
        pc = ['Project', 'Config']
        if key not in pc:
            GB.errstream('Project file key error: %s must be from %s' % (key, str(keys)))
            return
        openok =  self.openDatabase()
        if openok:
            self.database[key] = object
            self.closeDatabase()
        else:
            self.error("Unable to add %s to project file" % str(object))
            print "put: open was not ok"

    def BatchRun(self, id):
        " returns batch run object, or zero if unsuccessful "
        " database dictionary keys can be: 'Project', 'Config' or batch IDs "
        if self.openDatabase():
            if self.database.has_key(id):
                br = self.database[id]
                self.closeDatabase()
                return br
            else:
                self.error('Batch run ID %s not found in project file' % id)
                return 0
        else:
            return 0

    def addBatchRun(self, batchrun=None, id=None):
        if self.openDatabase():
            if id == None:
                id = str(batchrun.id)
            self.database[id] = batchrun
            self.closeDatabase()
        else:
            self.error("Unable to add %s to project file" % batchrun.batfile)

    def delBatchRun(self, id):
        if self.openDatabase():
            if self.database.has_key(id):
                del self.database[id]
            self.closeDatabase()
        else:
            self.error("Unable to delete %s from project file" % id)

    def RunList(self):
        rl = []
        if self.openDatabase():
            keys = self.database.keys()
            self.closeDatabase()
            for k in keys:
                if k == 'Project' or k == 'Config':
                    continue
                else:
                    rl.append(k)
        return rl

    def openDatabase(self, blocking=1, new=0):
        " shelve.open creates file if it doesn't exist "
        " if blocking set = 0, if can't get lock, returns immediately with value 0 "
        #if not new:
        #   if not os.path.exists(self.filename):
        #       self.error("unable to find %s" % self.filename)
        #       self.error("current directory %s" % os.getcwd())
        #       return 0
        if new:
            GB.outstream("openDatbase: creating new project file")
            
        #try:
        b = self.lock.acquire(blocking)
        if blocking == 0 and b == 0:
            self.error("openDatabase: unable to acquire lock")
            return 0

        self.database = shelve.open(self.filename)
        return 1
        #except:
        #   self.error("openDatabase error")
        #   return 0

    def closeDatabase(self):
        try:
            self.database.close()
            self.lock.release()
            return 1
        except:
            self.error("closeDatabase error")
            return 0

    def whichDatabase(self):
        from whichdb import whichdb
        print "project database appears to be: " + whichdb(self.filename)


####################################################################
# class for external database, e.g., MS SQL Server or MySQL

class SpiderDatabase:
    "all functions should be overridden by local database instances"
    def __init__(self):
        self.databaseName = ""  # refers to external database (eg, "MySQL")
        self.testquery = ""     # example or test SQL query
        self.projectquery = ""  # SQL that gets project info
        self.id = ""            # project id
        self.connection = None
        self._DATABASE = 'test' # eg, for MySQL 'use database' command
        self._USER = ''
        self._PASSWORD  = ''
        self._TABLE = 'projects'
        
        self.processArgs()

    def processArgs(self):
        pass

    # boolean (returns 0 or 1)
    def isExtDatabaseAlive(self):
        pass

    # getProjectInfo loads whatever information it can get from the database
    # into the SpiderProject object. In the worst case, nothing
    # is added and the object is unchanged (or returns a default object).
    def getProjectInfo(self):
        " expects GB.P.ID to contain the project ID"
        pass

    def sendQuery(self, query):
        pass

####################################################################
class threadPackage:
    " a simple container for thread variables. Turns out only function is used"
    def __init__(self, function=None, flag=None):
        if function != None:
            self.function = function
        if flag != None:
            self.flag = flag
        self.ttype = "threadpackage"
            
class threadObject(threading.Thread):
    def __init__(self, *args, **kwargs):
        self._stopevent = threading.Event()
        threading.Thread.__init__(self)

        self.args = args
        self.kwargs = kwargs
        if 'function' in kwargs:
            self.function = kwargs['function']
        else:
            self.function = ""
        self.package = threadPackage(function=self.function)

    ### override the run method ###
    def run(self):
        self.name = self.getName() # must be set after thread starts
        while not self._stopevent.isSet():
            pass

    def join(self):
        if hasattr(self,'waitevent'):  # some threads hang waiting for event flag
            self.waitevent.set()
        self._stopevent.set()
        threading.Thread.join(self)
    
####################################################################
# Configuration classes

class Config:
    """ spidui configuration for dialogs and directory structure.
        The configuration is independent of any project. """
    def __init__(self):
        # the following are attributes of the <Configuration> tag
        self.useParameterFile = 1
        self.useDatabase = 1
        #self.useprojID = 1
        self.Title = GG.bigLabeltxt
        self.Image = GG.mainImage
        self.helpurl = ""
        """ Dialogs: a dictionary with dialog name as key.
            see spiderDialog for Dialog class  """
        self.Dialogs = { 'dialogList' : [] }
        """ Dirs: a list of files, f, where f may be a
           1) a filename string, or
           2) a directory: [ "dirname" [ f,f,..]]   """
        self.Dirs = []
        self.path = [] # list of places to get batch files from

    def addDialog(self, dialog):
        "add to self.Dialogs; replace dialog, if it's already there"
        if dialog == None or dialog == "": return
        if hasattr(dialog, 'name'):
            if dialog.name not in self.Dialogs:
                self.Dialogs['dialogList'].append(dialog.name)
            self.Dialogs[dialog.name] = dialog   # replaces

    def addFile(self, filename, directory):
        pass

    def save(self):
        " saves to project database "
        if not hasConfig(): return
        if not hasattr(GB.P, 'projfile'): return
        GB.DB.put('Config', GB.C)  # puts GB.C under key 'Config'

    def save2xml(self, filename=None, setproject=0):
        saveConfig2xml(filename, config=self, setproject=setproject)

        
####################################################################

class saveConfig2xml:
    def __call__(self, file=None, config=None, setproject=0):
        self.init(file=file, config=config, setproject=setproject)
    def __init__(self, file=None, config=None, setproject=0):
        if file == None: file = GG.sysprefs.configFile
        try:
            fp = open(file,'w')
        except:
            GB.errstream("saveConfig2xml:file open error: %s" % (file))
            return

        if config == None: self.config = GB.C
        else: self.config = config
        C = self.config

        self.indent = 2
        self.B = []  # create the output list of lines
        
        configtag = "<Configuration"
        if hasattr(C, 'useParameterFile') and C.useParameterFile == 0:
            configtag += ' params="no" '
        if hasattr(C, 'useDatabase') and C.useDatabase == 0:
            configtag += ' database="no" '
        configtag += ">\n"
        self.writeln(configtag)

        # write title, image, help tags inside <Main> tag
        self.writeln("<Main>")
        sp = " " * self.indent
        if hasattr(C,'Title'):
            titletxt = sp + "<title>%s</title>" % C.Title
            self.writeln(titletxt)
        if hasattr(C,'Image'):
            titletxt = sp + "<image>%s</image>" % C.Image
            self.writeln(titletxt)     
        titletxt = sp + "<helpurl>%s</helpurl>" % GG.HelpURL
        self.writeln(titletxt)
        self.writeln("</Main>\n")
            
        self.writeln()
        self.writeLocations()
        self.writeDialogs()
        self.writeDirectories()
        self.writeln("</Configuration>")

        fp.writelines(self.B)
        fp.close()
        GB.outstream("configuration saved to %s" % file)
        if setproject:
            GB.C = C
            GB.outstream("configuration loaded from %s" % file)
            spiderGUtils.updateMainMenus()

    def writeln(self, line="", indent=0):
        sp = " " * indent
        self.B.append(sp + line + "\n")

    def write(self, line, indent=0):
        sp = " " * indent
        self.B.append(sp + line)

    def writetag(self, tag, data, indent=0):
        sp = " " * indent
        self.B.append(sp + "<%s>%s</%s>\n" % (tag, data, tag))

    def writeLocations(self):
        sp = " " * self.indent
        self.writeln("<Locations>")
        for item in self.config.path:
            self.writeln(sp + "<location>%s</location>" % item)
        self.writeln("</Locations>\n")

    def writeDialogs(self):
        dialogs = self.config.Dialogs 
        dk = dialogs['dialogList']
        #print "writeDialogs: dk %s" % str(dk)
        #print "writeDialogs: dialog keys %s" % str(dialogs.keys())
        if len(dk) == 0:
            return

        di = self.indent
        bi = di * 2
        self.writeln("<Dialogs>")
        for d in dk:
            dialog = dialogs[d]
            self.writeln("<dialog>", indent=di)
            self.writetag('name', dialog.name, indent=di)
            #print "writeDialogs: %s" % dialog.name
            self.writetag('title', dialog.title, indent=di)
            self.writetag('dir', dialog.dir, indent=di)
            self.writetag('help', dialog.help, indent=di)
            for item in dialog.cmdlist:
                if self.isButton(item):
                    self.writeButton(item, indent=bi)
                else:
                    groupname = item[0]
                    self.writeln('<group name="%s">' % groupname, indent=bi)  
                    blist = item[1]
                    for item in blist:
                        self.writeButton(item, indent=bi)
                    self.writeln("</group>", indent=bi)
            self.writeln("</dialog>", indent=di)
        self.writeln("</Dialogs>\n")

    def writeButton(self,button, indent=0):
        sp = " " * indent
        btntag = "<button"
        if len(button) > 3:
            run,edit = button[3]   # run, edit button attributes
            if run == 'no': btntag += ' run="no"'
            if edit == 'no': btntag += ' edit="no"'
            #print button
        btntag += ">"
        
            
        self.writeln(sp + btntag)
        self.writetag('label', button[0], indent=indent+2)
        self.writetag('buttontext', button[1], indent=indent+2)
        if len(button) == 3:
            proclist = button[-1]
        else:
            proclist = button[-2]
        self.writetag('proc', self.stringify(proclist), indent=indent+2)
        self.writeln(sp + "</button>")
        
    def isButton(self,b):
        if len(b) < 3: return 0
        if type(b[1]) == type("string"):
            return 1
        else:
            return 0

    def stringify(self, thing):
        if type(thing) == type(["list"]): # ['a','b','c'] -> "a,b,c"
            s = ""
            for item in thing:
                s += "," + str(item)
            s = s[1:]
        else:
            s = str(thing)
        return s


    # -----------------------------------------------
    class dirs2xml:
        """ create xml text from directory data structure """
        def __init__(self, data):
            self.text = ""
            for item in data:
                self.processData(item, level=0)
            self.text = self.text.replace(",</","</").strip()
            if self.text[-1] == ",":
                self.text = self.text[:-1]
            
        def processData(self, t, level):
            if len(t) < 2: return
            """ recursive function for directories """
            spacer = "    " * level
            if type(t) == type(["list"]):
                if len(t[1]) == 0:
                    self.text += spacer + '<dir name="%s"/>\n' % (t[0])
                else:
                    self.text += spacer + '<dir name="%s">\n' % (t[0])
                    for item in t[1]:
                        self.processData(item, level=level+1)
                    self.text += '</dir>\n'
            else:
                self.text += t + ","

    def writeDirectories(self):
        self.writeln("<Directories>")
        x = self.dirs2xml(self.config.Dirs)
        self.writeln(x.text)
        self.writeln("</Directories>")

####################################################################
"""
scrolledForm: a common GUI framework

standard keyword arguments (* = required)
   wintitle 
   title    *
   subtitle
   subtitlepos  (for the 'anchor' keyword)

   title_font
   bgd (bgd color for top and button frames, or can specify separately)
   bgd_top
   bgd_bottom
   foreground

Methods:
    __init__
    mktopFrame
    mkbuttonFrame
    adjustSize
    addButton
    helpMessage(widget, text)
    quit()
    
Methods to override:
    makeButtons(buttonframe, bgdcolor)
    processargs
    mkMainFrame  
"""
class scrolledForm:
    
    def __init__(self, **kwargs):
        keywords = kwargs.keys()
        self.kwargs = kwargs
        
        if "wintitle" in keywords:
            wt = kwargs["wintitle"]
        elif "title" in keywords:
            wt = kwargs["title"]
        else:
            wt = "Spire form"
        self.top = spiderGUtils.newWindow(wt)
        if self.top == 0:return

        self.child_windows = []
        # not actually child windows, but windows created by this app

        if GG.prefs.balloonHelp:
            self.balloon = spiderGUtils.myPmwBalloon(self.top)
        else: self.balloon = 0

        self.processargs()

        self.ftop = self.mktopFrame()
        self.sf = Pmw.ScrolledFrame(self.top,
                                    horizflex='expand',
                                    vertflex='expand',
                                    vscrollmode='dynamic')
        self.fmain = self.sf.interior()
        self.mkMainFrame()
        
        self.fbut = self.mkbuttonFrame()

        # pack the frames and check the resulting size.
        self.ftop.pack(side='top', fill='x', expand=0)
        self.fbut.pack(side='bottom', fill='x', expand=0)
	self.sf.pack(side='top', fill='both', expand=1)
	self.top.update_idletasks()
	self.adjustSize()

    # adjustSize tries to fit all the lines into the display.
    # If there are too many, it's displayed with a scrollbar.
    def adjustSize(self):
        # get the full screen size of the display
        xmax, ymax = self.top.winfo_screenwidth(), self.top.winfo_screenheight()
        maxht = int(0.9 * float(ymax))
        maxwd = int(0.7 * float(xmax))
        # get interior frame sizes
        wdtop, httop = self.ftop.winfo_reqwidth(), self.ftop.winfo_reqheight()
        wdmid, htmid = self.fmain.winfo_reqwidth(), self.fmain.winfo_reqheight()
        wdbut, htbut = self.fbut.winfo_reqwidth(), self.fbut.winfo_reqheight()
        totalht = htbut + htmid + httop

        height = htmid
        width = wdmid
        if totalht > maxht:
            height = maxht/2
        if wdmid > maxwd:
            width = maxwd
            
        self.sf.component("clipper").configure(height=height)
        self.sf.component("clipper").configure(width=width)
        self.top.update_idletasks()

    def mktopFrame(self):
        keywords = self.kwargs.keys()
        #defaults
        title = ""
        subtitle = ""
        subtitlepos = "center"
        textcolor = 'black'
        title_font = GG.spid.font['large']
        subtitle_font = GG.spid.font['small']
        
        if "title" in keywords:
            title = self.kwargs["title"]
        if "subtitle" in keywords:
            subtitle = self.kwargs["subtitle"]
        if "subtitlepos" in keywords:
            subtitlepos = self.kwargs["subtitlepos"]
        if "bgd" in keywords:
            bgd = self.kwargs["bgd"]
        elif "bgd_top" in keywords:
            bgd = self.kwargs["bgd_top"]
        else:
            bgd = GG.bgd01
        if "title_font" in keywords:
            title_font = self.kwargs["title_font"]
            subtitle_font = self.kwargs["title_font"]
        if "foreground" in keywords:
            textcolor = self.kwargs["foreground"]
            
        ftop = Frame(self.top, relief=GG.frelief, borderwidth=GG.brdr,
                     background=bgd)
        titlab = Label(ftop, text=title, font=title_font,
                       background=bgd, foreground=textcolor)
        sublab = Label(ftop, text=subtitle, font=subtitle_font,
                       background=bgd, foreground=textcolor) #,
                       #anchor=W, justify=LEFT)
        titlab.pack(side='top', pady=GG.pad2y)
        sublab.pack(side='top', pady=GG.pady, anchor=subtitlepos)

        if hasattr(self, 'helpmsg') and len(self.helpmsg)>0:
            self.helpMessage(ftop, self.helpmsg)

        return ftop
    
    def mkbuttonFrame(self):
        keywords = self.kwargs.keys()
        if "bgd" in keywords:
            bgd = self.kwargs["bgd"]
        elif "bgd_bottom" in keywords:
            bgd = self.kwargs["bgd_bottom"]
        else:
            bgd = GG.bgd01
            
        fbut = Frame(self.top, relief=GG.frelief, borderwidth=GG.brdr,
                     background=bgd)
        self.makeButtons(fbut)
        return fbut

    def addButton(self, frame, text, command, side='left', help=None):
        b = Button(frame, text=text, command=command)
        b.pack(side=side, padx=GG.padx, pady=GG.pady)
        if help != None:
            self.helpMessage(b, help)

    def helpMessage(self,widget,text):
        if self.balloon:
            self.balloon.add(widget,text)

    def quit(self):       
        self.top.update_idletasks()  # make sure all adjustments are done
        #if hasattr(self, 'child_windows'):
            # not strictly child windows, but windows this app has created
            #if self.top.winfo_exists(): print "============= %s " % self.top.title()
            #print "============= %s " % str(self.child_windows)
            #for child in self.child_windows:
            #   spiderGUtils.killWindow2(child)
        spiderGUtils.killWindow2(self.top)       

      
    # ============================================#
    " override this method "
    # ============================================#
    def makeButtons(self, buttonframe):
        self.addButton(buttonframe, text="Cancel", command=self.quit,
                       side='right', help = "Close this window")
            
    # ============================================#
    " override this method "
    # ============================================#
    def processargs(self):
        " kwargs is a dict; keywords is a list "
        keywords = self.kwargs.keys()
        
    # ============================================#
    " override this method "
    # ============================================#
    def mkMainFrame(self):
        fr = self.fmain
        keywords = self.kwargs.keys()
        for i in range(20):
            s = "Hello! this is line # %d" % i
            b = Label(fr,text=s, font=GG.spid.font['large'])
            b.pack(side='top')
        
