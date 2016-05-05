# $Id: spiderProj.py,v 1.2 2012/08/02 20:30:27 tapu Exp $
#
# Opens/Edits Spire projects

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
import os, shelve
from shutil import copy
from   Tkinter import *
import Pmw

import GB,GG
from   spiderUtils import *
from   spiderGUtils import *
import spiderParam
import spiderConfig
import spiderDButils
import spiderFilenums
import spiderClasses
import spiderFtypes
 
######################################################################
#
# PROJECT METHODS
#
# NEW, EDIT -->
#          (manual)   --> projForm(new)  --> projSet (save)
#          (database) --> projForm(edit) --> projSet (save)
#
#    most of the work done in projForm.readEntries()
#
# OPEN --> projOpen --> projSet (no save)

class rshTest(spiderClasses.threadObject):
    " call with host as argument "
    " __init__ and join() are in superclass. Override run() "

    def run(self):
        if 'host' in self.kwargs:
            self.host = self.kwargs['host']
        else:
            return
        
        GB.outstream.write("Testing rsh connection to %s...  " % self.host)
        testcmd = "date '+%H:%M:%S'"
        dateformat = re.compile('\d\d:\d\d:\d\d')
        cmd = 'rsh %s "%s"' % (self.host, testcmd)
        # TO dO ######### next line should get a timeout
        out = getoutput(cmd)
        if dateformat.search(out):
            GG.spidui.write_queue('GG.topwindow.bell()')
            GB.outstream("connection to %s is OK!" % self.host)
        else:
            GG.spidui.write_queue('GG.topwindow.bell()')
            GB.outstream("\nUnable to connect to %s" % self.host, 'red')
            GG.sysprefs.netexec = 'cancel'
    
def gotrsh(host):
    "uses a thread to test rsh connection"
    rsh = rshTest(host=host)
    rsh.start()

def askLocalorRemote(projecthost, localhost) :
    var = IntVar()
    var.set(0)
    w = newWindow('Select Local or Remote host')
    f1 = Frame(w, background=GG.bgd01, relief=GG.frelief, borderwidth=GG.brdr)
    txt  = "You are running this program on %s.\n" % localhost
    txt += "But the host for this project is %s.\n" % projecthost
    #txt += "This may greatly reduce the efficiency of SPIDER!"
    lbl= Label(f1, text=txt, background=GG.bgd01, anchor=W, justify='left')
    lbl.pack(padx=5, pady=5)
    f1.pack(side='top', fill='both', expand=1)

    remote_txt = 'Run SPIDER remotely on %s using rsh' % projecthost
    local_txt  = 'Run SPIDER locally on %s' % localhost
    
    Radiobutton(w, text=remote_txt, value=1,variable=var).pack(anchor='w')
    Radiobutton(w, text=local_txt, value=2, variable=var).pack(anchor='w')
    Radiobutton(w, text='Cancel', value=3,variable=var).pack(anchor='w')

    f1.waitvar(var)
    w.destroy()
    i = var.get()
    if i == 1: res = 'remote'
    elif i == 2: res = 'local'
    else: res = 'cancel'
    return res

def isBatchRun(br):
    # cannot get the following line to work:
    # if isinstance(br, spiderClasses.SpiderBatchRun):"
    b = str(br)
    if b.find("spiderClasses.SpiderBatchRun instance") > -1:
        if hasattr(br,'id'):
            #print "%s is a SpiderBatchRun instance" % br.id
            return 1
        else:
            #print "%s is a SpiderBatchRun instance, but has no id" % b
            return 0
    else:
        #print "%s is NOT a SpiderBatchRun instance" % b
        return 0

def printBatchRun(b):
    print "%s %s %s %s %s" % (b.id, b.batfile, b.dir, b.time_start, b.filenumbers)
    
def makeProjectTable():
    " project table is a dictionary indexed by run ID "
    if not hasProject(): return

    T = {}

    keys = GB.P.RunList  # RunList is a list if run IDs
    keys.sort()
    for key in keys:
        br = getBatchRun(key)
        if br != 0:
            #if isinstance(br, spiderClasses.SpiderBatchRun):  fails
            if isBatchRun(br):
                T[key] = br
                #printBatchRun(br)
            #else:
            #    print "%s is not a batch run object" % key
            #    #deleteBatchRun(key)
    return T
   
def projNew():
    projForm(mode='new')
    return

# uses data extension as project directory - appends it in dir entry box
def addext(event,eext,entdir):
    ext = eext.get()
    if ext == "": return
    dir = entdir.get()
    if os.path.basename(dir) == ext:
        return
    s = os.path.join(dir,ext)
    entdir.setentry(s)
    entdir.component('entry').xview(len(s))

# tries to get the remote hostname from the  project directory
def addhost(event,ehost,entdir):
    dir = entdir.get()
    if dir != "":
        host = getHost(dir)
        if host != "":
            ehost.setentry(host)

def projEdit():
    if hasProject():
        projForm('edit')
    else:
        projOpen()

def getconfiglist(configdir=None):
    if configdir == None:
        configdir = GG.sysprefs.configdir
    cfgs = os.listdir(configdir)

def put_item_first(alist, item):
    " make item the first element in the list "
    new = [item]
    for x in alist:
        if x != item:
            new.append(x)
    return new
"""
def getProjectDatabase(projfile):
    " sets GB.DB. Returns 1 if successful "
    #  creation of database instance creates a project file, if needed
    GB.DB = spiderClasses.ProjectDatabase(projfile)
    
    if not hasDatabase():
        GB.errstream("Unable to create a project file")
        return 0

    if hasattr(GB.DB, 'filename') and GB.DB.filename == projfile:
        return 1
    else:
        GB.errstream("getProjectDatabase: error opening %s" % (projfile))
        return 0
"""
    

###################################################################
# the Project Form

class projForm:
    def __call__(self, mode='new', pid=""):
        self.init(mode, pid)
    def __init__(self, mode='new', pid=""):
        if mode == 'new': title = 'New Project'
        elif mode == 'edit': title = 'Project ' + GB.P.ID

        w = newWindow(title)
        if w == 0: return
        self.w = w
        
        self.mode = mode        
        if pid == "" and hasProject('ID'): pid = GB.P.ID
        self.pid = pid
        
        # check the current directory for any config files
        lc = dirlist('.', "*.xml")
        localConfigs = []
        for cfg in lc:
            if spiderFtypes.isSpiderConfigFile(cfg):
                localConfigs.append("./" + cfg)

        if mode == 'edit':
            name = GB.P.title
            file = GB.P.projfile
            ext  = GB.P.dataext
            host = GB.P.host
            if host.strip() == "":
                host = gethostname()
            dir  = GB.P.projdir
            config = GB.P.config
            self.configlist = []
            if localConfigs:
                self.configlist = localConfigs
            if config not in self.configlist:
                self.configlist = [config] + self.configlist
            #self.loadEntries()
                
        elif mode == 'new':        # some defaults
            name = ext = ""
            file = 'proj001'
            host = gethostname()
            dir = getCurrentDir()
            # display a list of config files from default location and cwd
            config = GG.sysprefs.configFile # a default setting in Globals module
            defaultconfigdir = GG.sysprefs.configdir
            cfgs = dirlist(GG.sysprefs.configdir, "*.xml")
            self.configlist = []
            for cfg in cfgs:
                self.configlist.append(os.path.join(defaultconfigdir,cfg))
            if localConfigs:
                self.configlist = localConfigs + self.configlist
                
        self.configlist.sort()
        
        if 'simple2.xml' in self.configlist:
            put_item_first(self.configlist, 'simple2.xml')
        if 'simple.xml' in self.configlist:
            put_item_first(self.configlist, 'simple.xml')

        cwd = getCurrentDir()

        # see if the database/projectid frame is required
        fr0 = Frame(w, relief=GG.frelief, borderwidth=GG.brdr, background=GG.bgd01)
        fr1 = Frame(w, relief=GG.frelief, borderwidth=GG.brdr)
        fr2 = Frame(w, relief=GG.frelief, borderwidth=GG.brdr)
        fr3 = Frame(w, relief=GG.frelief, borderwidth=GG.brdr)
        bot = Frame(w, relief=GG.frelief, borderwidth=GG.brdr, background=GG.bgd01)
        px = 10
        py = 4

        # top frame with project ID - see if database is used
        self.epid = Pmw.EntryField(fr0, labelpos='w', value = pid,
                                label_text='Project ID: ')
        self.epid.component('entry').configure(width=7)
        self.epid.component('label').configure(background=GG.bgd01)
        self.epid.pack(side = 'left', anchor='w',expand=1, padx=px, pady=py+4)

        self.usedatabase = 1
        if hasConfig('useDatabase'):
            self.usedatabase = GB.C.useDatabase
        if GB.extDatabase and self.usedatabase != 0:
            dblbl = Label(fr0, text="Get project info from database:", background=GG.bgd01)
            fetch = Button(fr0, text='Get', command=self.getDatabaseInfo)
            fetch.pack(side='right', padx=5, pady=py+4)
            dblbl.pack(side='right', padx=5, pady=py+4)

        # Frame with entry fields
        self.ename = Pmw.EntryField(fr1, labelpos='w', value = name,
                                 label_text='Project title: ')
        self.ename.component('entry').configure(width=38)
        self.ename.pack(anchor='w',expand=1, padx=px, pady=py)
        
        self.efile = Pmw.EntryField(fr1, labelpos='w', value=file,
                                 label_text='Project file: ')
        self.efile.component('entry').configure(width=24)
        self.efile.pack(anchor='w',expand=1, padx=px, pady=py)
        
        self.eext = Pmw.EntryField(fr1, labelpos='w', value=ext,
                                label_text='Data extension (3 characters): ')
        self.eext.component('entry').configure(width=4)               
        self.eext.pack(anchor='w',expand=1, padx=px, pady=py)
        
        self.ehost = Pmw.EntryField(fr1, labelpos='w', value=host,
                                 label_text='Host machine: ')
        self.ehost.component('entry').configure(width=18)
        self.ehost.pack(anchor='w',expand=1, padx=px, pady=py)

        self.edir = Pmw.EntryField(fr2, labelpos='nw', value=dir+os.sep,
                                label_text='Directory for this project: ')

        # Frames with Directory and Configuration
        dirwidth = 32
        self.edir.component('entry').configure(width=dirwidth)
        x = len(cwd) - dirwidth
        self.edir.component('entry').xview(x)
        
        browseButton = Button(fr2, text="Browse",
                          command=Command(getDir2,self.edir,w))
        browseButton.pack(side='right', padx=px, pady=5)

        self.ecfg = Pmw.ComboBox(fr3, labelpos='nw',
                                 label_text='Configuration file: ',
                                 scrolledlist_items=self.configlist)
        mxwid = 0
        for item in self.configlist:
            if len(item) > mxwid:
                mxwid = len(item)
        self.ecfg.component('entryfield').component('entry').configure(width=mxwid)
        self.ecfg.selectitem(0)

        configButton = Button(fr3, text="Browse",
                          command=Command(getFile,self.ecfg.component('entryfield'),"*.xml"))
        configButton.pack(side='right', padx=px, pady=5)
        self.ecfg.pack(anchor='w', fill='x', expand=1, padx=px, pady=py)
        seeEntry(self.ecfg)
            
        self.edir.pack(anchor='w', fill='x', expand=1, padx=px, pady=py)
        seeEntry(self.edir)

        self.loadvar = IntVar()
        cb = Checkbutton(fr3, text='Create directories and load batch files',
                         variable=self.loadvar)
        cb.pack(anchor='w', side='bottom', padx=5,pady=5, fill='x', expand=1)
        if mode == 'new':  # or GB.extDatabase == 1:
            self.loadvar.set(1)
        else:
            self.loadvar.set(0)

        self.entries = [self.epid,self.ename,self.efile,self.eext,self.edir,self.ehost,self.ecfg]

        fr0.pack(side='top', fill='both')
        fr1.pack(side='top', fill='both')
        fr2.pack(side='top', fill='both')
        fr3.pack(side='top', fill='both')

        self.edir.bind('<Return>', self.readEntries)
        # next line automatically appends a 3-letter project directory ~datext
        #self.eext.bind('<FocusOut>', lambda event,e=self.eext,d=self.edir:
        #           addext(event,e,d))

        # Button frame
        okButton = Button(bot, text = "OK",
                          command=self.readEntries)
        quitButton = Button(bot, text = "Cancel",
                            command=w.destroy) 
        okButton.pack(side='left', padx=px, pady=5)
        quitButton.pack(side='right', padx=px, pady=5)
        bot.pack(side='bottom', fill='both')

        self.ename.component('entry').focus_set()
        
    def loadEntries(self):
        " copies GB.P project info into entry fields "
        if not hasProject(): return
        self.ename.setvalue(GB.P.title)
        self.efile.setvalue(GB.P.projfile)
        self.eext.setvalue(GB.P.dataext)
        self.edir.setvalue(GB.P.projdir)
        self.ehost.setvalue(GB.P.host)
        # self.ecfg is a ComboBox displaying self.configlist
        #self.ecfg.setvalue([GB.P.config])

    def getDatabaseInfo(self):
        " makes new GB.P, gets info from external database, writes to entries "
        id = self.epid.getvalue()
        if id == "" or not id.isdigit():
            displayError('Please enter a valid Project ID number')
            self.w.lift()
            return
        # create a new instance of a Project class
        GB.P = spiderClasses.SpiderProject(id=id)
        
        db = spiderDButils.createDatabaseInstance()
        if spiderDButils.getProjectInfo(db):   # puts project info into GB.P
            self.loadEntries()   # loads db info into project form
        del(db)

    def readEntries(self):
        # 1) check entries for legal values
        ProjID = self.epid.get().strip()
        name = self.ename.get().strip()
        projfile = self.efile.get().strip()
        ext  = self.eext.get().strip()
        if len(ext) > 0 and ext[0] == '.' and len(ext) > 1:
            ext = ext[1:]
        projdir  = self.edir.get().strip()
        host = self.ehost.get().strip()
        
        config = self.ecfg.get().strip()
        config = os.path.abspath(config)
        configpath,configfile = os.path.split(config)
        if configpath == os.getcwd():
            CONFIG_IN_CURRENT_DIR = 1
        else:
            CONFIG_IN_CURRENT_DIR = 0
        
        if name == '' or projfile == '' or ext == '' or projdir == '':
            displayError('Please fill in all the blanks','Error')
            self.w.lift()
            return
        elif len(ext) != 3:
            displayError('File extension must\nbe 3 letters long','Error')
            self.w.lift()
            return

        # 2) create the project directory, if it doesn't exists
        if not os.path.exists(projdir):
            if askOKorCancel("Create %s?" % (projdir),projdir + " does not exist"):
                if not makeDirectory(projdir):
                    displayError('Unable to access ' + projdir,'Error')
                    self.w.lift()
                    return
            else:
                return
            
        killWindow(self.w)

        if not hasProject():
            GB.P = spiderClasses.SpiderProject(id=ProjID)
            
        projdir = truepath(projdir)
        projfile = truepath(projfile)
        projdir, projext = os.path.splitext(projdir)  # no extension on project file
        config = truepath(config)
        chdir(projdir)

        # 3) set project attributes
        GB.P.ID = ProjID
        GB.P.title = name
        GB.P.projfile = os.path.basename(projfile)
        GB.P.dataext = ext
        GB.P.projdir  = projdir
        GB.P.host = host
        GB.P.config = config

        # 4) read config.xml file, put config in GB.C, write to local directory
        if config != "":
            if not os.path.exists(config):
                config = os.path.join(GG.sysprefs.configdir, config)
                if not os.path.exists(config):
                    displayError("Unable to find %s" % config)
                    GB.errstream("spiderProj.projEntries: unable to find %s" % config)
                    return
            c = spiderConfig.readXMLConfig(config)
            if c != 0:
                GB.C = c
                local = os.path.join(projdir, os.path.basename(config))
                if not CONFIG_IN_CURRENT_DIR:
                    GB.C.save2xml(local)
                GB.P.config = local
                GG.sysprefs.configFile = os.path.basename(config)
            else:
                GB.errstream("spiderProj.projEntries: unable to process config file")
     
        # 5) copy batch files to project directories
        loadbatch = self.loadvar.get()
        if isCurrentDirectory(GB.C.path):  # checks <location> tags
            loadbatch = 0
        if loadbatch:
            result = loadProject()
            if result == 0:
                GB.errstream("loadProject: error loading project")
                return

        # 6) set GB.DB to project file
        projfile = os.path.join(projdir,projfile)
        GB.DB = spiderClasses.ProjectDatabase(filename=projfile, new=1)
    
        if not hasDatabase():
            GG.topwindow.bell()
            GB.errstream("Unable to create a project file", 'red')
            return

        GB.DB.put('Project', GB.P)
        GB.DB.put('Config', GB.C)

        # 7) sets various graphical objects in Main window, save project
        projSet()
        projSave()
        
        # 8) Parameter file:
        #    First, see if config specifies 'no parameters'
        if hasConfig('useParameterFile') and GB.C.useParameterFile != 0:
            pass
        else:
            return
        # For a new project, see if Config had default parameters
        if self.mode == 'new' and hasattr(GB.C, 'parms'):
            # GB.C.parms will only be set if config.xml had a <Parameter> section
            parmdict = spiderParam.readParamTextfile(parmlist=GB.C.parms)
            if parmdict != None and len(parmdict) > 0:
                GB.outstream("Using default parameter list from %s" % config)
                spiderParam.presentParmForm(parmdict)
                return
                
        # if the parameter file exists, read it and present form
        parmfile = os.path.join(projdir,GG.sysprefs.paramFile)
        if os.path.exists(parmfile):
            spiderParam.readParmFile(filename=parmfile)
        # otherwise prompt user to create new one 
        else:
            spiderParam.parmNew(defaultfile=parmfile)
            
        
#------ end projForm -----------------------------------------

def isCurrentDirectory(path):
    " <location> tags may have 'current directory' "
    if type(path) == type(["list"]):
        path = str(path[0])  # convert to str cos of unicode [u'/usr/myproject/.']
    if path.find("current") > -1 and path.find("directory") > -1:
        return 1
    elif path == "." or path == os.getcwd():
        return 1
    else:
        return 0

def loadProject():
    if not hasProject():
        displayError('No project found')
        return 0
    if not hasConfig():
        displayError('Project does not have configuration loaded')
        return 0
    
    projdir = GB.P.projdir
    #print "loadProject: %s" % projdir
    if makeDirectory(projdir):
        chdir(projdir)
    else:
        return 0
    
    x = loadBatch()
    return 1
               

# returns 1 if all subdirectories found in pdir, 0 otherwise
def checkProj(dirlist):
    #print "checkProj"
    all_present = 1
    for d in dirlist:
        dir = d[0]
        subdirs = d[1]
        dd = os.path.join(pdir,d)
        if os.path.exists(dd):
            continue
        else:
            all_present = 0
            break
    return all_present

def changeLabel(label,text):
    if label == 'proj':
        if hasattr(GG.spidui,'projLabel'):
            GG.spidui.projLabel.configure(text='Project: ' + text)
    elif label == 'dir':
        if hasattr(GG.spidui,'dirLabel'):
            GG.spidui.dirLabel.configure(text='Directory: ' + text)

# Sets various graphical objects to values for this project.
def projSet():
    " returns 1 if successful"
    changeLabel('proj', GB.P.title)
    changeLabel('dir', GB.P.projdir)
    if hasConfig('Title'):
        GG.spidui.bigLabel.configure(text=GB.C.Title)
    if hasConfig('Image'):
        GG.spidui.putImage(GB.C.Image)

    if GG.sysprefs.filenumFile.strip() != "":
        GG.sysprefs.filenumFile = addExtension(GG.sysprefs.filenumFile, GB.P.dataext)
    #print GG.sysprefs.filenumFile
    
    # check for local parameter file first
    localparam = os.path.split(addExtension(GG.sysprefs.paramFile,GB.P.dataext))[1]
    currentparam = os.path.join(GB.P.projdir,localparam)
    if os.path.exists(currentparam):
        GG.sysprefs.paramFile = currentparam
    else :
        GG.sysprefs.paramFile = addExtension(GG.sysprefs.paramFile,GB.P.dataext)

    # figure out if they're running on the localhost
    projhost = GB.P.host
    localhost = getHost()
    if projhost == "" or projhost == None:
        projhost = localhost
        
    if projhost == localhost:
        GG.sysprefs.netexec = 'local'
    else:
        res = askLocalorRemote(projecthost=projhost, localhost=localhost)
        if res == 'remote':
            GG.sysprefs.netexec = 'remote'
            GB.outstream('local host: %s, remote host: %s' % (localhost, projhost))
            gotrsh(projhost) # if unsuccessful, sets GG.sysprefs.netexec = 'cancel'
        elif res == 'local':
            GG.sysprefs.netexec = 'local'
        else:
            return 0

    # try to figure out the project file path on this machine

    chdir(GB.P.projdir)
    
    if GG.prefs.savelogfile:
        logfilename = os.path.join(GB.P.projdir,newfilename(GG.sysprefs.logfile))
        GB.outstream.logfile = logfilename
        GB.errstream.logfile = logfilename
        GB.outstream("logfile is " + logfilename)
        GB.outstream.uselogfile = 1
        GB.errstream.uselogfile = 1

    GB.P.T = makeProjectTable()
    return 1
        
#----------------------------------------------------------------    
def projOpen(filename=None):
    if filename == None:
        filename = askfilename()
    if filename == "":
        return

    # if it's a path, try to change to the directory with the project file
    projpath = None
    if os.sep in filename:
        projpath, filename = os.path.split(filename)
        if not chdir(projpath):
            txt = "projOpen: Unable to change to %s" % projpath
            print txt
            return

    #  set GB.DB to project file (spiderClasses.ProjectDatabase)
    GB.DB = spiderClasses.ProjectDatabase(filename=filename)

    if not hasDatabase():
        GB.errstream("unable to open project file %s" % filename)
        return

    # obtain project, runlist, config from the project file (database)
    project = GB.DB.get('Project')

    if project:
        GB.P = project

        # make sure database has correct project filename 
        cwd = os.getcwd()
        if cwd in GB.P.projdir or GB.P.projdir in cwd:
            GB.P.projdir = cwd
        else:
            GB.outsream("Project directory is no longer %s?\n" % GB.P.projdir)
            if os.path.exists(filename):
                GB.outsream("Changing project directory to: %s\n" % cwd)
                GB.P.projdir = cwd
            else:
                return

        if not remoteProjectPath(GB.P.projdir, projpath):
            GB.errstream("unable to find project directory")
            return
        
        GB.P.RunList = GB.DB.RunList() # compute runlist from the projfile

        config = GB.DB.get('Config')        
        if config:
            GB.C = config
        else:
            if GB.P.config != "" and os.path.exists(GB.P.config):
                config = spiderConfig.readXMLConfig(GB.P.config)
                if not config:
                    GB.errstream("spiderProj.projOpen: Unable to load configuration.")
                else:
                    GB.C = config
                    
        projfile = os.path.join(GB.P.projdir,GB.P.projfile)
        GB.DB.filename = projfile

    else:
        displayError(filename + " doesn't appear to contain a valid project.")
        return

    if not projSet():
        GB.outstream('Project not loaded')
        return
    
    GB.outstream("\nProject: %s, ID: %s\n" % (GB.P.title,GB.P.ID))
    prjtxt = "%s opened " % (os.path.join(GB.P.projdir,GB.P.projfile))
    prjtxt = prjtxt + time.asctime(time.localtime(time.time()))
    GB.outstream(prjtxt)
    getParms()   # load GB.Parameters
    
    if hasProject() and hasConfig():
        updateMainMenus()
        # if there's a filenums file, load it into File Numbers Entry
        if GG.sysprefs.filenumFile.strip() != "":
            filenumfile = os.path.join(GB.P.projdir, GG.sysprefs.filenumFile)
            a = spiderFilenums.openFileNumbers(filenumfile)
            if a != []:
                fn = spiderFilenums.range2string(spiderFilenums.list2range(a))
                GG.disp_fnums.set(fn)

def goprojSave():
    if hasProject():
        if hasattr(GB.P,'projfile'):
            projSave()
    else:
        displayError('No project to save')

#-----------------------------------------------------------------
#
# expandTargets: from GB.C.Dirs, construct [(bat,target),(bat,target) , ...]
# where target dir is always relative to project directory.
# GB.C.Dirs=  [dir [list]] where list items may be strings (files), or
# directories with pattern [dir [list]] (i.e., it's recursive)
def expandTargets(dlist=None, args=None):
    if dlist == None:
        dlist = GB.C.Dirs
    projdir = GB.P.projdir
    N = []
    for item in dlist:
        #print "in expandTargets : %s" % str(item)
        tdir = item[0]   # dir, from item =  [dir, [list of files, dirs]]
        titems = item[1] # list
        if tdir == '.':
            target = projdir
        else:
            if args == None:
                target = os.path.join(projdir, tdir)
            else:
                target = os.path.join(projdir, args, tdir)
            
        for t in titems:
            if type(t) == type("string"):
                N.append( [t, target] )
            elif type(t) == type(["list"]):
                N = N + expandTargets([t], tdir)
    return N

def mkprojdirs(dirobj):
    "dirobj = [dirname, [files, dirs]] "
    if len(dirobj) < 2: return
    ddir = dirobj[0]
    items = dirobj[1]
    # create the directory if it doesn't already exist
    if ddir != '.' and not os.path.exists(ddir):
        if not makeDirectory(ddir):
            GBerrstream("unable to create %s" % ddir)
            return

    # create any subdirectories
    cwd = os.getcwd()
    chdir(ddir)
    for item in items:
        if type(item) == type(["list"]):
            mkprojdirs(item)
    chdir(cwd)

def loadBatch():
    "copy batch files from src locations to target directories"
    if not hasProject():
        displayError('spiderProj.loadBatch: No project found')
        return 0
    if not hasConfig():
        displayError('spiderProj.loadBatch: No configuration loaded')
        return 0

    write_all = 0
    no_overwrite = 0
    done = 0
    ovar = IntVar()

    # Get list of source directories (some may not be found)
    srcdirs = []
    for loc in GB.C.path:
        if os.path.exists(loc):
            srcdirs.append(loc)
    if len(srcdirs) == 0:
        GB.errstream("UNABLE TO FIND SOURCE DIRECTORY FOR BATCH FILES")
        return 0
    #print "load batch, srcdirs : %s" % str(srcdirs)

    # create subdirectories under project directory
    if not chdir(GB.P.projdir):
        GB.errstream("spiderProj.loadbatch: UNABLE TO FIND PROJECT DIRECTORY")
    for item in GB.C.Dirs:
        mkprojdirs(item)
    # from GB.C.Dirs, construct [(bat,target),(bat,target) , ...]
    batchlist = expandTargets()
    GB.outstream("Searching source directories:")
    for sdir in srcdirs:
        GB.outstream("%s" % sdir)
            
    # for each batch file: 1) search srclist til it's found, 2) check overwrite
    # settings, 3) copy it into target directory   
    for b in batchlist:
        bat = b[0]
        targetdir = b[1]
        batchpath = ""
        for sdir in srcdirs:
            if os.path.exists(sdir):
                batchpath = os.path.join(sdir,bat)
                if os.path.exists(batchpath):  # found the source
                    if not os.path.exists(targetdir):
                        if not makeDirectory(targetdir):
                            continue
                        
                    # see if the file is already in the target directory
                    targetfile = os.path.join(targetdir, bat)
                    if write_all == 0:
                        if os.path.exists(targetfile):
                            w = newWindow('Overwrite?')
                            overwriteDialog(targetfile, w, ovar)
                            GG.topwindow.wait_window(w)
                            s = ovar.get()
                            if s == 1:   # yes, overwrite
                                pass
                            elif s == 2: # no
                                break
                            elif s == 3: # overwrite all
                                write_all = 1  
                            elif s == 4: # copy without overwrite
                                no_overwrite = 1
                                write_all = 1
                                break
                            else:       # cancel
                                done = 1
                                return 1
                    elif write_all == 1:
                        if os.path.exists(targetfile) and no_overwrite:
                            break   # option 4

                    # copy the file
                    if checkFileAccess(targetdir):
                        copy(batchpath,targetdir)
                        GB.outstream("copying %s to %s" % (batchpath,targetdir))
                        break  # don't search any more src directories
                    else:
                        GB.outstream("write permission needed for %s" % targetdir)
                else:
                    batchpath = ""  # not found
                    
        if batchpath == "":
            GB.errstream("Cannot find %s" % bat)

    return 1

def overwriteDialog(filename, w, var):
    w.title('Warning')
    f = Frame(w, background = GG.bgd01, relief=GG.frelief, borderwidth=GG.brdr)
    ovtxt = filename + ' already exists. Overwrite?'
    Label(f, background = GG.bgd01, text=ovtxt).pack(side='left', padx=5, pady=5)
    f.pack(side='top', fill='both', expand=1)
    
    Radiobutton(w, text='Yes', value=1,
                variable=var).pack(anchor='w')
    Radiobutton(w, text='No, do not overwrite', value=2,
                variable=var).pack(anchor='w')
    Radiobutton(w, text='Overwrite all', value=3,
                variable=var).pack(anchor='w')
    Radiobutton(w, text="Copy all new files, but don't overwrite old", value=4,
                variable=var).pack(anchor='w')
    Radiobutton(w, text='Cancel batch file copying', value=5,
                variable=var).pack(anchor='w')
    var.set(1)
    fb = Frame(w, background = GG.bgd01, relief=GG.frelief, borderwidth=GG.brdr)
    b = Button(fb, text='Ok', command=w.destroy)
    b.pack(padx=5, pady=5)
    fb.pack(side='bottom', fill='both', expand=1)
