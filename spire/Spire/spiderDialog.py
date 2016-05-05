# $Id: spiderDialog.py,v 1.1 2012/07/03 14:21:59 leith Exp $
#
# functions for Spire Dialog windows
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
import Pmw
import GB,GG
from   spiderUtils import *
from   spiderGUtils import *
import spiderBatform
import spiderBatch
from spiderClasses import scrolledForm, SpiderProject, Config
from spiderParam import replaceTagwithParam

# button : ['Create doc file', 'ord.bat', ['ord.bat']]
#  group : ['Refinement', [buttonlist]]
# ergo, check 2nd item to see if it's a button or a button group

def isButton(b):
    " button vs a group "
    if len(b) < 2: return 0
    if type(b[1]) == type("string"):
        return 1
    else:
        return 0

"""
class Dialog:
  [ name, title, dir, help, cmdlist]
e.g.,
name: Particles
title: Particle Picking and Selection
dir : projdir/Particles    # programs executed in this dir
help: help URL
cmdlist: a list of buttons or button groups. cmdlist = [b,b,g]
    group: a list with one name, and a list of one or more buttons.
           g = ["name", [b, b, ..] ]
           name can be empty string
    button: a list with label, buttontext followed by list of one or more programs.
           b = [ "compute spectra", "power", [power.bat, pnums.bat, ..] ]
           label can be empty string
           New: 4th element may be run/edit flags (run,edit), where run and edit
           may be "no" or "".
A program may be either a batch file or "<prog>something else</prog>" enclosed
in <prog> tags.

"""
class Dialog:
    def __init__(self,name = "",
                 title = "",
                 dir = "",
                 help = "",
                 cmdlist = []):
        self.name = name
        self.title = title
        self.dir = dir.strip()
        if self.dir == "":
            self.dir = '.'
        self.help = help
        self.cmdlist = cmdlist

    def addBatch(self, label, filename):
        newbutton = [label, filename, [filename]]
        self.cmdlist.append(newbutton)
        
def dummy():
    pass

execGreen = "#60E090"

class DialogWindow(scrolledForm):
    """ Dialog used to launch programs """
    
    def processargs(self):
        keywords = self.kwargs.keys()
        self.dialog = self.kwargs["dialog"]
        self.progstring = StringVar()
        
    def makeButtons(self, buttonframe):
        self.addButton(buttonframe, text="Help", command=self.helpme,
                       help = "open the manual page")
        self.addButton(buttonframe, text="Cancel", command=self.quit,
                       side='right', help = "Close this window")
        
    def helpme(self):
        spiderHelp(self.dialog.help)
   
    def mkMainFrame(self):
        fr = self.fmain
        dialog = self.dialog
        #keywords = self.kwargs.keys()
        self.bwidth = 0
        for item in dialog.cmdlist:     # get max button width
            if isButton(item):
                bw = len(item[1])
                if bw > self.bwidth: self.bwidth = bw
            else:  # group
                buttonlist = item[1]
                for b in buttonlist:
                    bw = len(b[1])
                    if bw > self.bwidth: self.bwidth = bw
        k = 0
        for item in dialog.cmdlist:
            if isButton(item):
                self.addProgButton(fr, item, row=k)
            else:
                groupname = item[0]
                blist = item[1]
                frg = Pmw.Group(fr, tag_text=groupname)
                frg.grid(row=k, column=0, columnspan=3, sticky=NSEW, padx=5, pady=5)
                fg = frg.interior()
                frg.component('ring').configure(borderwidth=GG.brdr+2)
                #frg.component('tag').configure(background=GG.bgd02)
                fgrow = 0
                for button in blist:
                    self.addProgButton(fg, button, row=fgrow)
                    fgrow += 1                            
            k = k+1

    def isProg(self, prog):
        " <prog> vs a batch file "
        if string.find(string.lower(prog),"<prog>") > -1:
            return 1
        else:
            return 0

    def addProgButton(self, frame, button, row):
        label = button[0]
        btxt = button[1]
        cmdlist = button[2]
        # the Label
        Label(frame, text=label).grid(row=row, column=0, sticky=E, padx=5, pady=5)
        # the Run button
        b = Button(frame, text=btxt, width=self.bwidth, activebackground=execGreen,
                   command=Command(self.runBatch,cmdlist))
        b.grid(row=row, column=1, sticky=E, padx=5, pady=5)
        # the Edit button
        if self.isProg(cmdlist[0]):
            " <prog>external program</prog> "
            #progstr = cmdlist[0]
            progstr = self.checkString(cmdlist[0])  # remove <prog> tags
            progstr = replaceTagwithParam(progstr)  # checks for Cs, kV, pixsize
            #self.progstring.set(progstr)
            e = Button(frame, text='Edit')
            e.configure(command=Command(self.editProg,progstr,cmdlist,b,e))
            self.helpMessage(e,"Edit " + progstr)
        else:
            " regular Spider batch file "
            progstr = self.checkString(cmdlist)
            batstr = self.no_args(progstr)
            e = Button(frame, text='Edit', command=Command(self.editBatch,cmdlist))
            self.helpMessage(e,"Display " + batstr + " in a batch form")
        e.grid(row=row, column=2, sticky=E, padx=5, pady=5)

        # check for new run,edit attributes
        if len(button) > 3:
            run,edit = button[3]
            if run == 'no' or run == '0':
                b.configure(state='disabled')
            if edit == 'no' or edit == '0':
                e.configure(state='disabled')
        
        self.helpMessage(b,"Run " + progstr)
        
        
    def runBatch(self, cmdlist):
        spiderBatch.runbatch([self.dialog.dir,cmdlist])
       
    def no_args(self, cmdstr):
        " strip Spider command line args "
        blist = cmdstr.split(",")
        out = []
        for item in blist:
            i = item.split()
            out.append(i[0])
        x = stringify(out)
        return x

    def editBatch(self, commandlist):
        " cmdlist is a list, but only has 1 string of files "
        cmdstr = self.no_args(commandlist[0])
        cmdlist = cmdstr.split(",")

        dir = self.dialog.dir
        revlist = []
        for item in cmdlist:
            revlist.append(item)
        revlist.reverse()

        for batchfile in revlist:
            batch = batchfile.strip()
            if dir != '.':
                fullname = os.path.join(GB.P.projdir,dir,batch)
            else:
                fullname = os.path.join(GB.P.projdir,batch)
            spiderBatform.getBatch(fullname)

    def editProg(self, progstr, cmdlist, runbutton, editbutton):
        " if edited, changes must be made to Run.cmd, Run.help, Edit.cmd, Edit.hlp"
        w = newWindow("command line")
        if w == 0: return

        self.progstring.set(progstr)
        slen = len(progstr)
        entry = Entry(w, textvariable=self.progstring, width=slen).pack(side='top', fill='x', expand=1)
        ok = Button(w, text='ok', command=w.destroy).pack(padx=2, pady=2)
        w.wait_window(w)

        progstr = self.progstring.get()
        newprogstr = '<prog>' + progstr + '</prog>'
        cmdlist[0] = newprogstr

        runbutton.configure(command=Command(self.runBatch, cmdlist))
        self.helpMessage(runbutton, "Run " + progstr)
        editbutton.configure(command=Command(self.editProg, progstr, cmdlist, runbutton, editbutton))
        self.helpMessage(editbutton,"Edit " + progstr)
     
    def checkString(self,cmdlist):
        #print "checkString in %s" % str(cmdlist)
        s = str(cmdlist)
        for item in ['<prog>','<PROG>','</prog>','</PROG>','[',']']:
            if s.find(item) > -1:
                s = s.replace(item,"")
        #print "checkString: %s" % s
        return s


#########################################################################
#
#  class DialogEditForm: for editing dialogs
#  class ButtonFrame: an editable button widget
#  class GroupFrame:  a button group widget

selectColor = "#FFFCCC"

class DialogEditForm:
    """ presents a scrolled form for creating/editing dialogs """
    def __init__(self, w, dialog=None):
        w.protocol("WM_DELETE_WINDOW", self.quit)

        self.w = w
        if dialog != None:
            self.dialog = dialog
        else:
            self.dialog = Dialog()
                
        self.result = "cancel"
        self.child_windows = []

        ftop = Frame(w, background = GG.bgd01, relief=GG.frelief, borderwidth=GG.brdr)
        nlabel = Label(ftop, background = GG.bgd01, text= '(short) Name: ')
        en = StringVar()
        en.set(self.dialog.name)
        ename = Entry(ftop,textvariable=en)

        tlabel = Label(ftop, background = GG.bgd01, text= 'Title: ')
        et = StringVar()
        et.set(self.dialog.title)
        etitle = Entry(ftop,textvariable=et)
        
        ed = StringVar()
        ed.set(self.dialog.dir)
        dirwidth = 32
        edir = Entry(ftop,textvariable=ed, width=dirwidth)
        seeEntry(edir)
        dlabel = Button(ftop, text="Directory:", background = GG.bgd01,
                        command=Command(getDir,ed,edir))
        
        eh = StringVar()
        eh.set(self.dialog.help)
        ehelp = Entry(ftop,textvariable=eh)
        seeEntry(ehelp)
        hlabel = Button(ftop, text="Help URL:", background = GG.bgd01,
                        command=Command(getFile,eh))

        nlabel.grid(row=0, column=0, padx=5, pady=5, sticky='e')
        ename.grid(row=0,column=1, padx=5, pady=10, sticky='ew')
        tlabel.grid(row=1, column=0, padx=5, pady=5, sticky='e')
        etitle.grid(row=1,column=1, padx=5, pady=10, sticky='ew')
        dlabel.grid(row=2, column=0, padx=5, pady=5, sticky='e')
        edir.grid(row=2,column=1, padx=5, pady=10, sticky='ew')
        hlabel.grid(row=3, column=0, padx=5, pady=5, sticky='e')
        ehelp.grid(row=3,column=1, padx=5, pady=10, sticky='ew')
        ftop.pack(side='top', fill='x', expand=0)

        self.entries = (ename, etitle, edir, ehelp)

        # ---- button groups ----
        self.sf = Pmw.ScrolledFrame(w, borderframe=14, horizflex='expand',
                                    usehullsize=1, hull_height=300)
        self.sf.pack(fill='both', expand=1)
        self.gframe = self.sf.interior()
        self.gframe.configure(background=GG.bgd03)
        self.buttonlist = []

        self.pdy = 5
        self.pdx = 2*self.pdy

        for bg in self.dialog.cmdlist:
            if isButton(bg):
                b = ButtonFrame(bg, parent=self.gframe)
            else:
                b = GroupFrame(bg, parent=self.gframe)
            b.frame.pack(side='top', fill='x', expand=1, padx=self.pdx, pady=self.pdy)
            self.buttonlist.append(b)
            
        self.sf.reposition()

        # ----- bottom frame ----
        fbot = Frame(w, background = GG.bgd01, relief=GG.frelief, borderwidth=GG.brdr)
        okbut = Button(fbot, text="OK", command=self.okDone)
        addbut = Button(fbot, text=" Add button",
                        command=Command(self.addButton))
        delbut = Button(fbot, text="Delete",
                        command=Command(self.delButton))
        prebut = Button(fbot, text="Preview",
                        command=self.previewDialog)
        quitbut = Button(fbot, text='Cancel',command=self.quit)
        
        okbut.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        addbut.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')
        delbut.grid(row=0, column=2, padx=5, pady=5, sticky='nsew')
        prebut.grid(row=0, column=3, padx=5, pady=5, sticky='nsew')
        quitbut.grid(row=0, column=4, padx=5, pady=5, sticky='e')
        fbot.pack(side='bottom', fill='x', expand=0)

    def clearButtonFrame(self):
        for b in self.buttonlist:
            b.frame.pack_forget()
            
    def repackButtonFrame(self):
        for b in self.buttonlist:
            b.frame.pack(side='top', fill='x', expand=1, padx=self.pdx, pady=self.pdy)        

    def delButton(self):
        # REDO THIS - MUST BE SIMPLIFIED
        " button = [ label, btn_txt, [program, program, ..]] "
        newlist = []
        found = 0
        for b in self.buttonlist:
            if b.type == "button" and b.selected:
                b.destroy()
                found = 1
                
            elif b.type == "group" and b.selected:
                b.destroy()
                found = 1

            elif b.type == "group" and not b.selected:
                newbb = []
                for bb in b.buttonlist:
                    if bb.selected:
                        bb.destroy()
                        found = 1
                    else:
                        newbb.append(bb)
                    
                if len(newbb) > 0:
                    b.buttonlist = newbb
                    newlist.append(b)
                    
            else:
                newlist.append(b)
                
        if not found:
            displayError('Nothing selected')
        else:
            self.buttonlist = newlist
            self.sf.reposition()

    def addButton(self):
        " add above the selected button. If none selected, add to bottom"
        " button = [ label, btn_txt, [program, program, ..]] "
        nb = [ "", "",[""]]
        newbutton = ButtonFrame(nb, parent=self.gframe)

        newbuttonlist = []
        added = 0
        for button in self.buttonlist:
            if button.selected and added == 0:
                newbuttonlist.append(newbutton)
                added = 1
            newbuttonlist.append(button)
        if not added:
            newbuttonlist.append(newbutton)
        self.buttonlist = newbuttonlist
        self.clearButtonFrame()
        self.repackButtonFrame()
        self.sf.yview(mode='moveto', value=1)
        
    def okDone(self):
        " set new dialog values "
        self.getValues()
        missingtxt = ""
        if self.dialog.name == "": missingtxt = "Name"
        if self.dialog.title == "": missingtxt = "Title"
        if self.dialog.dir == "": missingtxt = "Directory"
        if missingtxt != "":
            displayError("Please fill in the\n'%s' field" % missingtxt)
        else:
            self.result = "ok"
            self.quit()

    def previewDialog(self):
        tmpdialog = Dialog()
        self.getValues(dialog=tmpdialog)
        w = windowExists(tmpdialog.name)
        if w != 0:
            killWindow(w)
        makeDialogWindow(tmpdialog)
        #dwin = makeDialogWindow(tmpdialog)
        #if hasattr(self, 'child_windows'):
        #   if dwin not in self.child_windows:
        #       self.child_windows.append(dwin)
        #else:
        #   self.child_windows = [dwin]

    def getValues(self, dialog=None):
        """ put values from entries into dialog instance """
        if dialog == None:
            dialog = self.dialog
        dialog.name  = string.strip(self.entries[0].get())
        dialog.title = string.strip(self.entries[1].get())
        dialog.dir   = string.strip(self.entries[2].get())
        dialog.help  = string.strip(self.entries[3].get())

        cmdlist = []
        for b in self.buttonlist:
            if hasattr(b,'type') and b.type == "button":
                label = b.label.get()
                btxt = b.btntxt.get()
                p = b.progs.get()
                progs = p.split(",")  # make it a list
                btn = [label, btxt, progs]
                cmdlist.append(btn)
            else:
                # b.type = "group"
                name = b.grplabel.get()
                blist = []
                for btn in b.buttonlist:
                    label = btn.label.get()
                    btxt = btn.btntxt.get()
                    p = btn.progs.get()
                    progs = p.split(",")  # make it a list
                    bttn = [label, btxt, progs]
                    blist.append(bttn)
                cmdlist.append( [name, blist] )

        dialog.cmdlist = cmdlist
        
    def quit(self):
        " kill the preview windows, if any "
        w = windowExists(self.dialog.name)
        if w != 0:
            killWindow(w)
        #self.w.update_idletasks()  # make sure all adjustments are done
        #if hasattr(self, 'child_windows'):
        #   # not strictly child windows, but windows this app has created
        #   if self.w.winfo_exists(): print "------------- %s " % self.w.title()
        #   print "------------- %s " % str(self.child_windows)
        #   for child in self.child_windows:
        #       killWindow2(child)
        self.w.destroy()
    
# ----- end DialogEditForm ----------------------------------------------

class ButtonFrame:
    " btn = [ label, btn_txt, [cmd, cmd..] ]  "
    " Has a frame attribute, to be packed by the parent "
    def __init__(self, btn, parent):
        if len(btn) < 3: return
        self.type = "button"
        self.frame = Frame(parent, relief='groove', borderwidth=2)
        fr = self.frame

        self.selected = 0
        self.label = StringVar()
        self.btntxt = StringVar()
        self.progs = StringVar()

        self.label.set(btn[0])
        self.btntxt.set(btn[1])
        self.progs.set(stringify(btn[2]))

        l1 = Label(fr,text="Label: ")
        l1.grid(row=0,column=0, sticky='w')
        Entry(fr, textvariable=self.label).grid(row=0,column=1, sticky=W+E)
        l2 = Label(fr,text="Button text: ")
        l2.grid(row=1,column=0, sticky='w')
        Entry(fr, textvariable=self.btntxt).grid(row=1,column=1, sticky=W+E)
        l3 = Label(fr,text="Program(s): ")
        l3.grid(row=2,column=0, sticky='w')
        Entry(fr, textvariable=self.progs).grid(row=2,column=1, sticky=W+E)
        self.frame.columnconfigure(1, weight=2) # lets the entries expand
        self.labels = [l1,l2,l3]

        self.selcolor = selectColor
        self.bgd = self.frame.cget('background')
        self.frame.bind('<1>', self.select)
        l1.bind('<1>', self.select)
        l2.bind('<1>', self.select)
        l3.bind('<1>', self.select)

    def select(self,event):
        current = self.frame.cget('background')
        if current == self.bgd:
            color = self.selcolor
            self.selected = 1
        else:
            color = self.bgd
            self.selected = 0

        self.frame.configure(background=color)
        for label in self.labels:
            label.configure(background=color)

    def deselect(self):
        self.selected = 0
        color = self.bgd
        self.frame.configure(background=color)
        for label in self.labels:
            label.configure(background=color)

    def destroy(self):
        self.frame.pack_forget()
        del(self)

class GroupFrame:
    " grp = [ label, [btn, btn,..] ] "
    def __init__(self, group, parent):
        if len(group) < 2: return
        
        self.type = "group"
        self.selected = 0
        self.name = group[0]
        btnlist = group[1]
        bgd = GG.bgd02
        self.frame = Frame(parent, relief='groove', borderwidth=4,
                           background=bgd)
        
        self.grplabel = Pmw.EntryField(self.frame, labelpos='w',
                                       label_text = "Group label: ",
                                       value = self.name)
        labellabel = self.grplabel.component('label')
        labellabel.configure(background=bgd)
        self.grplabel.pack(side='top',fill='x', expand=1, pady=8)

        self.buttonlist = []
        for btn in btnlist:
            if isButton(btn):
                b = ButtonFrame(btn, parent=self.frame)
                b.frame.pack(side='top', fill='x', expand=1, padx=8, pady=4)
                self.buttonlist.append(b)

        self.selcolor = selectColor
        self.bgd = self.frame.cget('background')
        self.frame.bind('<1>', self.select)
        labellabel.bind('<1>', self.select)

    def select(self,event):
        current = self.frame.cget('background')
        if current == self.bgd:
            color = self.selcolor
            self.selected = 1
        else:
            color = self.bgd
            self.selected = 0

        self.frame.configure(background=color)
        self.grplabel.component('label').configure(background=color)

    def destroy(self):
        for b in self.buttonlist:
            b.frame.pack_forget()
            del(b)
        self.frame.pack_forget()
        del(self)

#
# Dialog Edit classes above
########################################################################
    
def makeDialogWindow(dialog):
    projdir = os.path.basename(GB.P.projdir)
    if dialog.dir == ".":
        dialogdir = projdir  # top-level directory
    else:
        dialogdir = os.path.join(projdir, dialog.dir) + os.sep  # subdirs
        
    tf = DialogWindow(wintitle=dialog.name,
                      title=dialog.title,
                      subtitle=dialogdir,
                      dialog=dialog)
    return tf
    
def editDialog(dialogname=None):
    if not hasProject():
        GB.P = spiderClasses.SpiderProject(name="noname",
                                           title="notitle",
                                           ID="000000")
    if not hasConfig():
        GB.C = Config()
        
    if dialogname != None and GB.C.Dialogs.has_key(dialogname):
        dialog = GB.C.Dialogs[dialogname]
    else:
        dialog = Dialog()
        
    w = newWindow("Edit Dialog")
    if w == 0: return
    df = DialogEditForm(w, dialog) # puts data in dialog, not df
    w.wait_window(w)
    if df.result == "ok":
        GB.C.addDialog(dialog)
        updateMainMenus()
