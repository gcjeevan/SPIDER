# $Id: spiderGUtils.py,v 1.3 2012/08/02 03:09:24 tapu Exp $
#
# graphic utilities used by many modules

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

import string
import os, sys
import cPickle
import re
import threading, time
import types, webbrowser
from   Tkinter import *
import Pmw
import tkFont
from   tkMessageBox   import askyesno, showerror, askokcancel
from   tkFileDialog   import askopenfilename, asksaveasfilename, askdirectory
from   tkCommonDialog import Dialog

import GB,GG
from spiderUtils import *
import spiderPlot
import spiderImage
import spiderFtypes
import spiderTree

#from prettyprint import dumpObj   # for debugging

# Redefined Pmw.Balloon because of errors when destroying other widgets.
# When toplevel windows contain widgets with balloon help, they should have
# a quit method that unbinds all the balloon help first (i.e. include 'pop').
#
# create instance:     bloon = myPmwBalloon(self.top)
# to add balloons:     bloon.add(widget, text)
# before self.top.destroy(), call bloon.pop()
class myPmwBalloon(Pmw.Balloon):
    " don't redefine __init__ "

    def add(self, widget, text):
        # create widget list the first time it's called
        if not hasattr(self, 'widgets'):
            self.widgets = []
        self.bind(widget, text)
        self.widgets.append(widget)

    def pop(self):
        for w in self.widgets:
            #print "popping %s" % str(w)
            try:
                self.unbind(w)
            except:
                pass


def noProjectError():
    displayError('Please open a project', 'No SPIRE project')
    
# thingy for the quick 'Edit/Run' menu full of batch files
def makeMenus(dirs):
    dirlist = []
    for d in dirs:
        name = d[0]
        if name == '.':
            name = GB.project_dir_title
        contents = d[1]
        flist = []
        for item in contents:
            if not isinstance(item,types.ListType):
                if len(item) > 4 and item[-4] == '.':
                    flist.append(item)   # must have 3-letter extension
        GB.M[name] = flist
        dirlist.append(name)
    GB.M['dirlist'] = dirlist
    #print GB.M
    
def updateMainMenus():
    makeMenus(GB.C.Dirs)
    GG.spidui.makeDialogMenu()
    GG.spidui.makeBatchMenu()
    GG.spidui.makeSequenceMenu()

# returns window if new window,
# returns 0 if one with same title is already opened
def newWindow(title):
    winlist = GG.topwindow.winfo_children()
    for win in winlist:
        if win.winfo_class() == 'Toplevel':
            if title == win.title():
                win.lift()
                return 0
    w = Toplevel(GG.topwindow)
    w.title(title)
    # set up icon
    icon = Toplevel(w)
    Label(icon, image=GG.icon).pack()
    w.iconwindow(icon)
    
    return w

def isToplevel(win):
    if hasattr(win, 'winfo_exists'):
        if win.winfo_exists():
            if win.winfo_class() == 'Toplevel':
                return 1
    return 0

# boolean, similar to newWindow, but doesn't create a window.
# If window with name='title' exists, returns window, else 0.
def windowExists(title):
    winlist = GG.topwindow.winfo_children()
    for win in winlist:
        try:
            winexists = win.winfo_exists()  # was crashing on Linux
        except:
            winexists = False
            #print "spiderGUtils: exception in windowExists"
        #print "winexists=%s" % str(winexists)
        if winexists:
            try: # even if winexists, the next line may get 'bad window path name'
                if win.winfo_class() == 'Toplevel':
                    if title == win.title():
                        return win
            except:
                return 0
    return 0

def killWindow(win):
    if win.winfo_exists():
        win.destroy()
        if win.winfo_exists():
            win.update_idletasks()

def killWindow2(win):
    " win can be a window title, Toplevel, or Class instance "
    " if a Class instance, try calling its quit method "
    if type(win) == type("string"):
        #print "killWindow2: win is a string: %s" % win
        w = windowExists(win)
        if w: killWindow(w)
    elif isToplevel(win):
        #print "killWindow2: win is a Toplevel: %s" % win.title()
        killWindow(win)
    elif hasattr(win, 'quit'):
        #print "killWindow2: win has a quit method: %s" % str(win)
        win.quit()
    else:
        print "killWindow2: %s" % str(win)
    
def callPlotData(plotfile=None):
    # check if Gnuplot.py is available
    if not spiderPlot.hasGnuplot():
        txt = spiderPlot.Gnuplot_promo()
        displayError(txt)
        return
    
    if plotfile == None:
        plotfile = askfilename()
    if not os.path.exists(plotfile):
        displayError('Unable to find %s' % plotfile)
        return
    if plotfile == "":
        return

    # check that it's a doc file before calling Gnuplot
    typelist = spiderFtypes.getFileType(plotfile)
    #print "callplotdata typelist %s" % str(typelist)
    if len(typelist) > 1 and typelist[1] == 'Document':
        pass
    else:
        if not askOKorCancel('This does not appear to be a Spider doc file.\n Continue?',
                             'Warning'):
            return
    callPlotDataQ(plotfile)

# quick version that skips file checking
def callPlotDataQ(plotfile):
    if hasattr(GG,'gnuplot') and GG.gnuplot != None:
        GG.gnuplot.add2list(plotfile)
    else:
        GG.gnuplot = spiderPlot.MyGnuplotPlot(GG.topwindow,[plotfile])
"""
def callDisplayImage(file=None):
    if file == None or not os.path.exists(file):
        file = askfilename()
    if file == "" or file == None:
        return
    spiderImage.displayImage(file)
"""
def showbusycursor():
    if GG.haveBusy:
        Pmw.showbusycursor()

def donebusycursor():
    Pmw.hidebusycursor()


def spiderHelp(url):
    if url != "" and url != None:
        #print "opening %s" % url
        wb = webbrowser.get()
        if hasattr(wb, 'open'):
            webbrowser.open(url)
        
def makeCommand(cmd):
    if GG.sysprefs.netexec == 'local':
        return cmd
    shellcmd = GG.sysprefs.remotecmd  # rsh or ssh
    host = GB.P.host
    rcmd = "%s %s '%s'" % (shellcmd, host, cmd)
    return rcmd

def getMaster(widget):
    if widget.master.winfo_class() != 'Toplevel':
        return getMaster(widget.master)
    else:
        if widget.master.winfo_exists():
            return widget.master
    
def liftMaster(widget):
    m = getMaster(widget)
    m.lift()

def displayError(message, title=None, parent=None):
    if title == None: title = 'Error'
    # check if called by main thread
    if isMainThread():
        showerror(title, message)
        if parent != None:
            parent.lift()
    else:
        #print "displayError called by secondary thread"
        msg = "showerror('%s', '%s')" % (title, message)
        GG.spidui.write_queue(msg)

def askOKorCancel(message, title=None, parent=None):
    if title == None:
        title = 'Warning'
    if isMainThread():
        try:
            if parent != None:
                ret = askokcancel(title, message, parent=parent)
            else:
                ret = askokcancel(title, message)
        except:
            print "askokcancel exception. "
            print "message: " + str(message)
            print "title : " + str(title)
            ret = 1

    else:
        ret = threadedGUIcall()
        
    return ret

def askYesorNo(message, title=None, parent=None):
    " returns True or False "
    if title == None: title = 'Warning'
    if parent != None:
        ret = askyesno(title, message, parent=parent)
    else:
        ret = askyesno(title, message)
    return ret

# returns "" if user hits 'cancel'
def askfilename():
    " if you hit 'cancel', askopenfilename returns an empty tuple "
    f = askopenfilename()
    if type(f) == type(()):
        return ""
    else:
        f = string.replace(f,"/tmp_mnt","")
        return f
    

def askSaveAsFilename(filetypes=None, initialfile=None):
    " returns empty string if unsuccessful"
    ft = []
    if filetypes != None:
        ft.append( (filetypes,filetypes )) # "*.dat" --> ("*.dat", "*.dat")
    if initialfile == None:
        f = asksaveasfilename(filetypes=ft)
    else:
        f = asksaveasfilename(filetypes=ft, initialfile=initialfile)
    if type(f) == type(()):
        return ""
    else:
        #f = string.replace(f,"/tmp_mnt","")
        return f
    
# askdirectory stuff for Python2.0
class Chooser(Dialog):
    command = "tk_chooseDirectory"
    def _fixresult(self, widget, result):
        if result:
            # keep directory until next time
            self.options["initialdir"] = result
        self.directory = result # compatibility
        return result

#def askdirectory(**options):
#    "Ask for a directory name"
#    return apply(Chooser, (), options).show()

def askDirectory():
    directory = askdirectory(initialdir=os.getcwd(),mustexist=1)
    return directory


def getDir(stringvar, entry=None):
    directory = askdirectory(initialdir=os.getcwd(),mustexist=1)
    stringvar.set(directory)
    if entry != None: seeEntry(entry)
    
def getDir2(entry, parent=None):
    directory = askdirectory(initialdir=os.getcwd(),mustexist=1, parent=parent)
    entry.setentry(directory)
    #parent.lift()

# put rightmost part of string in viewable field
def seeEntry(entry):
    " first check if it's a simple Entry or Pmw.EntryField"
    if hasattr(entry, 'widgetName') and entry.widgetName == 'entry':
        ent = entry
    elif hasattr(entry, '_entryFieldEntry'):
        ent = entry.component('entry')
    else:
        return
    s = len(ent.get())         # length of string
    w = int(ent.cget('width')) # width of entry
    if s > w:
        ent.xview(s-w)
    
# getFile utility for browse buttons attached to entry fields
def getFile(entry, filetypes=None):
    ft = []
    if filetypes != None:
        ft.append( (filetypes,filetypes )) # "*.dat" --> ("*.dat", "*.dat")
    ft.append(("All files", "*"))
    filename = askopenfilename(filetypes=ft)
    if len(filename) == 0: return 0

    # is it a simple entry or a Pmw.EntryField or a StringVar
    doc = entry.__doc__
    if doc == None and hasattr(entry,'setentry'):    # Pmw
        if hasattr(GB, 'P') :     # in spiderProj, GB.P.dataext may not be defined
            split = os.path.splitext(filename)
            extension = '.' + GB.P.dataext
            if extension == split[1] : filename = split[0]
        entry.setentry(filename)
    elif doc.find("Entry widget") > -1:      # Entry
        pass #tv = entry.configure('textvariable')
        #print tv
    elif doc.find("strings variable") > -1:  # StringVar
        if hasattr(GB, 'P') :     # in spiderProj, GB.P.dataext may not be defined
            split = os.path.splitext(filename)
            extension = '.' + GB.P.dataext
            if extension == split[1] : filename = split[0]
        entry.set(filename)
    return 1


def getFiles(parent=None, filetypes=None, entry=None):
    ft = []
    if filetypes != None:
        ft.append( (filetypes,filetypes )) # "*.dat" --> ("*.dat", "*.dat")
    ft.append(("All files", "*"))
    f = askopenfilename(parent=parent, multiple=1, filetypes=ft)
    # askopenfilename returns a tuple
    if entry == None:
        ft = []
        for file in f:
            ft.append(file)
        return ft
    else:
        # set the entry to a string of the filenames
        files = ""
        for file in f:
            base = os.path.basename(file)
            files += base + ","
        files = files[:-1]
        doc = entry.__doc__
        if doc == None and hasattr(entry,'setentry'):    # Pmw
            entry.setentry(files)
        elif doc.find("Entry widget") > -1:      # Entry
            pass #tv = entry.configure('textvariable')
            #print tv
        elif doc.find("strings variable") > -1:  # StringVar
            entry.set(files)


# ##########################################################

class addBatchWindow:
    def __init__(self,filename=None, dialog=None, label=None):
        self.w = newWindow(title = "Add batch file")
        if self.w == 0: return

        # -------------------------------
        top = Frame(self.w, background=GG.bgd01, relief=GG.frelief,
                    borderwidth=GG.brdr)
        top.pack(side='top', fill='x', expand=1)
        Label(top,text="Add a batch file to a dialog",
              background=GG.bgd01).pack()

        # -------------------------------
        mid = Frame(self.w)
        mid.pack(side='top', fill='both', expand=1)
        # dialog pulldown menu
        self.dialogs = []
        if hasConfig():
            for d in GB.C.Dialogs['dialogList']:
                if d == '.':
                    self.dialogs.append(GB.project_dir_title)
                else:
                    self.dialogs.append(d)
        
        self.dialog = Pmw.ComboBox(mid,label_text='Dialog: ',
                                   labelpos='w',
                                   scrolledlist_items=self.dialogs)
        if dialog != None and dialog in self.dialogs:
            self.dialog.selectitem(dialog)
        self.dialog.pack(side='top', fill='x', expand=1, padx=4,pady=4)
        # label entry
        self.label = Pmw.EntryField(mid, labelpos='w',
                                    label_text="Label: ")
        self.label.pack(side='top', fill='x', expand=1, padx=4,pady=4)
        if label != None:
            self.label.setvalue(label)
        # file entry
        self.batfile = Pmw.EntryField(mid, labelpos='w',
                                    label_text="Filename : ")
        self.batfile.pack(side='left', fill='x', expand=1, padx=4,pady=4)
        if filename != None:
            self.batfile.setvalue(filename)
        browse = Button(mid, text="Browse",
                        command=Command(getFile,self.batfile))
        browse.pack(side='right', padx=4,pady=4)
        
        # -------------------------------
        bot = Frame(self.w, background=GG.bgd01, relief=GG.frelief,
                    borderwidth=GG.brdr)
        bot.pack(side='bottom', fill='x', expand=1)
        ok = Button(bot, text='Ok', command=self.addBatch)
        quit = Button(bot, text='Cancel', command=self.w.destroy)
        ok.pack(side='left', padx=4,pady=4)
        quit.pack(side='right', padx=4,pady=4)

    def addBatch(self):
        dialogname = self.dialog.get()
        if dialogname == GB.project_dir_title:
            dialogname = '.'
        label = self.label.getvalue()
        filename = self.batfile.getvalue()
        #print dialog, label, filename
        self.w.destroy()
        
        #spiderConfig.addBatch(dialog, label, filename)
        if not hasConfig():
            return
        
        file = os.path.basename(filename) # filename should be the full path
        dialogname = dialogname.strip()

        # add a new button to the dialog
        dialog = GB.C.Dialogs[dialogname]
        dialogdir = dialog.dir.strip()
        if not os.path.exists(os.path.join(dialogdir,file)):
            os.system("cp %s %s" % (filename, dialogdir))
        dialog.addBatch(label, file)

        # add file to configuration's Directory list
        dirs = GB.C.Dirs
        dd = ""
        for item in dirs:
            if type(item) == type(["list"]):
                dname = string.strip(item[0])
                #print "%s %s %d %d" % (dname, dialogdir, len(dname),len(dialogdir))
                if item[0] == dialogdir:
                    item[1].append(file)
                    dd = dname
                    break
        if dd == "":
            print dialogdir + " not found in configuration"
            return
        updateMainMenus()

        # save the new config to the xml file and to project database
        GB.outstream("%s added to %s, configuration updated." % (file, dialog.name))
        GB.C.save2xml(GB.P.config)   # writes to xml file
        GB.DB.put('Config', GB.C)    # puts configuration in project database

def addBatch(filename=None, dialog=None, label=None):
    abwin = addBatchWindow(filename,dialog,label)

# ##########################################################

class textWindow:
    def __init__(self, title=None, font=None, toptext=None, importfile=None):
        if title == None: title = "view object"
        self.w = newWindow(title)
        if self.w == 0: return

        if toptext != None:  # add a label to the top
            self.toptext = Label(self.w, text=toptext)
            self.toptext.pack(side='top', padx=5, pady=5)

        self.textbox = Pmw.ScrolledText(self.w)
        if font in ['small', 'medium','large','output']:
            self.textbox.component('text').configure(font=GG.spid.font[font])
        self.textbox.pack(side='top', fill='both', expand=1)

        if importfile !=None and os.path.exists(importfile):
            self.textbox.importfile(fileName=importfile)

        # defined tags
        self.textbox.component('text').tag_configure('hdr', background='white',
                                                     relief='groove', borderwidth=2)

    def write(self, string, tag=None):
        if not self.hasTextbox(): return
        if tag == None:
            self.textbox.component('text').insert(END, str(string)+'\n')
        else:
            self.textbox.component('text').insert(END, str(string)+'\n', tag)
        self.textbox.see(END)
        self.w.update_idletasks()
        
    def clear(self):
        if self.hasTextbox(): self.textbox.delete("1.0",END)

    def hasWindow(self):
        if self.w.winfo_exists(): return 1
        else: return 0

    def hasTextbox(self):
        if self.hasWindow() and hasattr(self,'textbox'): return 1
        else: return 0

    def putToptext(self, msg):
        if self.hasTextbox(): self.toptext.configure(text=msg)
        
    def quit(self):
        self.w.destroy()

class editWindow:
    def __init__(self, file=None, title=None, font='output'):
        if file != None and not os.path.exists(file):
            print "\7"
            GB.errstream("Cannot find %s" % file)
            return
        
        #B = fileReadLines(file)
        #if B == None:
            #return

        if title == None: title = file
        if title == None: title = "edit window"
        self.w = newWindow(title)
        if self.w == 0: return
        
        if title != "edit window":
            toptext = title
        else:
            toptext = ""
        self.toptext = Label(self.w, text=toptext)
        self.toptext.pack(side='top', padx=5, pady=5)

        # the main text window
        self.textbox = Pmw.ScrolledText(self.w)
        if font in ['small', 'medium','large','output']:
            self.textbox.component('text').configure(font=GG.spid.font[font])
        self.textbox.pack(side='top', fill='both', expand=1)
        self.textbox.importfile(file)
        #for line in B:
            #self.textbox.write(line)

        # buttons at bottom
        fb = Frame(self.w, relief=GG.frelief, borderwidth=GG.brdr, background=GG.bgd01)
        fb.pack(side='bottom', fill='x', expand=1)
        if file != None:
            self.filename = file
            save = Button(fb, text='Save', command=self.save)
            save.pack(side='left', padx=4, pady=4)
        saveas = Button(fb, text='Save as', command=self.saveas)
        saveas.pack(side='left', padx=4, pady=4)
        quit = Button(fb, text='Quit', command=self.quit)
        quit.pack(side='right', padx=4, pady=4)

    def write(self, string):
        self.textbox.component('text').insert(END, str(string)) #+'\n')
        self.textbox.see(END)
        self.w.update_idletasks()
    def clear(self):
        self.textbox.delete("1.0",END)
    def quit(self):
        self.w.destroy()
    def save(self):
        self.textbox.exportfile(self.filename)
    def saveas(self):
        self.filename = askSaveAsFilename()
        if self.filename != "":
            self.save()

def textBoxInsert(textbox, text):
    textbox.component('text').insert(END, str(text)+'\n')
    textbox.see(END)

                
def viewFile(filename=None, type=None, verbose=0):  #0):
    " type can be 'text' (simple viewer), 'edit' (editor), 'image' (display) "
    if verbose: print "viewFile: %s" % filename
    if filename == None: filename = askfilename()
    if filename == "" or len(filename) == 0: return
    if not os.path.exists(filename):
        filename = truepath(filename)
        if not os.path.exists(filename):
            GB.errstream("Unable to find %s" % filename)
            return

    if type != None:
        if type == 'text':
            fn = os.path.basename(filename)
            tw = textWindow(title=fn, font='output', importfile=filename)
        elif type == 'edit':
            fileEdit(filename)
        elif type == 'image':
            spiderImage.displayImage(filename)
            if verbose:
                GB.outstream("displaying %s ..." % filename)
        elif type == 'volume':
            spiderImage.displayVolume(filename)
            if verbose:
                GB.outstream("displaying %s ..." % filename)

    elif type == None:
        # see if it has the project extension (i.e., a Spider file)
        base, ext = os.path.splitext(filename)
        extnodot = ext[1:]
        if extnodot == GB.P.dataext:
            if verbose: print "viewFile: %s is a Spider file" % filename
            if spiderFtypes.istextfile(filename):
                fileEdit(filename)
            elif spiderFtypes.isSpiderBin(filename):
                spiderImage.displayImage(filename)         
                if verbose:
                    GB.outstream("displaying %s ..." % filename)
        elif ext in GG.sysprefs.AppDict:
            if verbose: print "viewFile: %s is NOT a Spider file" % filename
            app = GG.sysprefs.AppDict[ext]
            executeCommand(app, [filename])
        else:
            if verbose: print filename

def fileEdit(file=None):
    if file == None: file = askfilename()
    if file == "": return
    
    cmd = "%s %s &" % (GG.prefs.editor, file)
    #print cmd
    try:
        os.system(cmd)
    except:
        displayError("Unable to open editor")

re_comment =  re.compile('; +/ *\w*')   # looks for patterns: " ; / comment"

# read parameter file, put in project settings
# loads GB.P.parameters as a side effect, returns list of values
def getParms():
    vlist = []  # a list of values
    parmfile = GG.sysprefs.paramFile
    if os.path.exists(parmfile) != 1: return vlist

    B = fileReadLines(parmfile)
    if B == None: return vlist
    P = {}
    plist = []   # list of [key, value, comment] items

    # needs to handle both the old format:
    # ; /       pixel size (A)
    #    5 1    3.720000
    #
    # and new format:
    #     5 1    4.780000     ; pixel size (A)
    n = len(B)
    ptr = 0
    while ptr < n:
        line = B[ptr].strip()
        if len(line) == 0:
            ptr += 1
            continue
        
        if line[0] == ';':
            # see if it's a comment line, followed by data
            if re_comment.match(line):
                line = line.replace(';','',1)
                line = line.replace('/','',1)
                comment = line.strip()
                ptr = ptr + 1
                line = B[ptr].split()   # get next data line
                if len(line) < 3:
                    ptr = ptr + 1
                    continue
                try:
                    key = int(line[0])
                    iii = int(line[1])
                    val = float(line[2])
                except:
                    ptr = ptr + 1
                    continue
                plist.append( [key, line[2], comment] )
        else:
            # new format, look for " 5 1    4.780000     ; pixel size (A) "
            s = line.split()
            if len(s) < 4:
                ptr = ptr + 1
                continue
            try:
                key = int(s[0])
                iii = int(s[1])
                val = float(s[2])
                if line.find(';') > -1:
                    ss = line.split(';',1)
                    comment = ss[1]
                else:
                    comment = "(no label found)"
                plist.append( [key, s[2], comment] )
            except:
                ptr = ptr + 1
                continue
        ptr = ptr + 1
        
    # construct dictionary (P) and valuelist (vlist) from plist
    for item in plist:
        key = item[0]
        value = item[1]
        P[key] = item
        vlist.append(value)
        
    if hasProject():
        GB.P.parameters = P
        # set the 3 global parms cs, kv, pixsize
        for item in plist:
            value   = item[1]
            comment = item[2].lower()
            if comment.find('spherical aberration') > -1:
                GB.P.Cs = value
            elif comment.find('electron energy') > -1:
                GB.P.kv = value
            elif  comment.find('pixel size') > -1:
                GB.P.pixelsize = value
            
    return vlist

def makeVBOFFwindow():
    var = IntVar()
    var.set(0)
    w = newWindow('VB OFF Error')
    f1 = Frame(w, background=GG.bgd01, relief=GG.frelief, borderwidth=GG.brdr)
    txt  = "This batch file has MD = VB OFF. This reduces the size of\n"
    txt += "the results file when there are many output data files.\n"
    txt += "But Spire cannot save all output files to the project with VB OFF!"
    lbl= Label(f1, text=txt, background=GG.bgd01, anchor=W, justify='left')
    lbl.pack(padx=5, pady=5)
    f1.pack(side='top', fill='both', expand=1)
    
    Radiobutton(w, text='Change to VB ON', value=1,
                variable=var).pack(anchor='w')
    Radiobutton(w, text='Proceed with VB OFF, dont save files to project',
                value=2, variable=var).pack(anchor='w')
    Radiobutton(w, text='Cancel operation', value=3,
                variable=var).pack(anchor='w')

    f1.waitvar(var)
    w.destroy()
    res = ""
    i = var.get()
    if i == 1: res = 'change'
    elif i == 2: res = 'proceed'
    elif i == 3: res = 'cancel'
    return res
    
####################################################################
# USER INTERFACE

def writeUserPrefs(verbose=0):
    local = 0
    prefsFile = GG.interface.file
    if GG.prefs.useLocalPrefsFile and hasProject():
        local = 1

    outlines = []  
    # everything in GG.prefs is a string except for colors and fonts
    # (they're objects with their own 'stringify' methods)
    colorstr = GG.prefs.colors.stringify()
    fontstr = GG.prefs.font.stringify()

    prefdict = GG.prefs.__dict__
    keys = prefdict.keys()
    for k in keys:
        if k == 'colors':
            outlines.append("%s: %s\n" % (k, colorstr))
        elif k == 'font':
            outlines.append("%s: %s\n" % (k, fontstr))
        else:
            value = prefdict[k]
            if not local and hasProject():    # remove extension
                if type(value) == type("string") and value[-3:] == GB.P.dataext:
                    value = os.path.splitext()[0]
            else:
                value = str(prefdict[k])
            outlines.append("%s: %s\n" % (k, value))

    # everything in GG.sysprefs is a string, except for AppDict
    prefdict = GG.sysprefs.__dict__
    keys = prefdict.keys()
    for k in keys:
        outlines.append("%s: %s\n" % (k, str(prefdict[k])))

    if fileWriteLines(prefsFile, outlines) and verbose:
        GB.outstream("current settings saved to %s" % prefsFile)

def readUserPrefs(verbose=1):
    " writes out user prefs if the file isn't there "
    filename = GG.interface.file
    if not os.path.exists(filename):
        writeUserPrefs(0)
    else:
        B = fileReadLines(filename)
        if B == None:
            showerror('File Open Error')
            return

        D = {}
        for line in B:
            if line.find(':') < 0:
                continue
            s = line.split(':',1)
            key, value = s[0], s[1].strip()
            D[key] = value

        #if 'useLocalPrefsFile' in D:
        #   GG.prefs.useLocalPrefsFile = int(D['useLocalPrefsFile'])

        keys = D.keys()
        for key in keys:
            value = D[key]

            # see if value is a dictionary
            if len(value) > 0 and value[0] == '{' and value[-1] == '}':
                value = eval(value)
                #print "%s is a dictionary: %s" % (key, str(value.keys()))

                if key == 'colors':
                    GG.prefs.colors.setAttributes(value)
                elif key == 'font':
                    GG.prefs.font.font = value
                elif key == 'AppDict':
                    GG.sysprefs.AppDict = value
                    
            elif type(value) == type("string"):
                # see if it's an integer
                try:
                    value = int(value)
                except:
                    pass

                # some values should have the project extension
                if hasProject() and key in ['filenumFile', 'paramFile']:
                    base, ext = os.path.splitext(value)
                    if ext == '':
                        value = value + '.' + GB.P.dataext
                    elif ext == '.':
                        value = value + GB.P.dataext
                    elif ext != GB.P.dataext:
                        value = base + '.' + GB.P.dataext

                # set values in GG.prefs and GG.sysprefs
                if hasattr(GG.prefs, key):
                    try:
                        value = int(value)
                        exec("GG.prefs.%s = %d" % (key, value))
                    except:
                        exec("GG.prefs.%s = '%s'" % (key, value))
                elif hasattr(GG.sysprefs, key):
                    try:
                        value = int(value)
                        exec("GG.sysprefs.%s = %d" % (key, value))
                    except:
                        exec("GG.sysprefs.%s = '%s'" % (key, value))

                if key == 'editor' and value not in GG.editorlist:
                    GG.editorlist.append(value)

        # set shortcuts
        GG.interface = GG.SysInterface()   # create a new instance
        GG.interface.user = GG.prefs
        GG.interface.system = GG.sysprefs
        if GG.prefs.useLocalPrefsFile == 0 or not hasProject():
            GG.interface.file = os.path.join(os.environ['HOME'],".spire")
        else:
            GG.interface.file = os.path.join(GB.P.projdir, '.spire')
        GG.spid = GG.prefs.font
        GG.colors = GG.prefs.colors
        GG.sysbgd = GG.colors.background
        GG.bgd01 = GG.colors.bgd01
        GG.bgd02 = GG.colors.bgd02
        GG.bgd03 = GG.colors.bgd03
    

def XXXwriteUserPrefs(verbose=0):
    GG.interface.user = GG.prefs
    GG.interface.system = GG.sysprefs
    filename = GG.interface.file
    try:
        P = GG.interface
        f = open(filename,'w')
        cPickle.dump(P,f)
        f.close()
        if verbose:
            GB.outstream("current settings saved to %s" % filename)
    except IOError, e:
        showerror('File Save Error', e)

def XXXreadUserPrefs(verbose=1):
    " writes out user prefs if the file isn't there "
    return
    filename = GG.interface.file
    if not os.path.exists(filename):
        writeUserPrefs(0)
    else:
        try:
            f = open(filename, 'r')
            GG.interface = cPickle.load(f)
            f.close()
            if verbose:
                GB.outstream("settings loaded from %s" % filename)
        except IOError, e:
            showerror('File Open Error', e)
            return
        # shortcuts
        GG.prefs = GG.interface.user
        GG.sysprefs = GG.interface.system
        GG.spid = GG.prefs.font
    
def showUserPrefs():
    out = GB.outstream
    prefs = GG.prefs
    keys = prefs.__dict__.keys()
    for k in keys:
        #out("%s: %s" % (k, str(prefs.__dict__[k])))
        print("%s: %s" % (k, str(prefs.__dict__[k])))
        
    prefs = GG.sysprefs
    keys = prefs.__dict__.keys()
    for k in keys:
        #out("%s: %s" % (k, str(prefs.__dict__[k])))
        print("%s: %s" % (k, str(prefs.__dict__[k])))

def fontSize(font=None):
    if font == None: font = GG.spid.font['medium']
    # converts font descriptor into tkFont family
    tkfont = tkFont.Font(font=font)
    test = Label(GG.topwindow, text='test',font=tkfont)
    height = tkfont.metrics('ascent') + tkfont.metrics('descent')
    width = tkfont.metrics('linespace')
    return (height, width)

def fontMeasure(text, font=None):
    if font == None: font = GG.spid.font['medium']
    # converts font descriptor into tkFont family
    tkfont = tkFont.Font(font=font)
    return tkfont.measure(text)

def treeview(topdir=None):
    spiderTree.startTree(ddir=topdir)   #(root=win, dir=ddir)

def notImplemented():
    displayError('That feature is not yet implemented', 'Sorry!')
