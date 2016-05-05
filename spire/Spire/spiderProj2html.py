# $Id: spiderProj2html.py,v 1.1 2012/07/03 14:21:59 leith Exp $
#
# Write Spire project information to html file

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
from spiderGUtils import *
from spiderUtils import *
from spiderClasses import scrolledForm, SpiderBatchRun

LabelDict = {'title': 'Title', 'ID': 'ID', 'projdir': 'project directory',
             'projfile': 'project file', 'dataext': 'data extension',
             'config': 'configuration', 'host': 'host'}

def proj2html():
    if not hasProject():
        displayError("Please open a project")
        return
    lbltxt = ""
    for att in ['title', 'ID', 'projdir', 'projfile', 'dataext', 'config', 'host']:
        if hasattr(GB.P, att):
            value = eval("GB.P." + att)
            if value != "":
                lbltxt += "%s : %s\n" % (LabelDict[att], value)

    # firt open a window to get filename (and Notes) from user.
    # When window closes, it calls saveProj2html
    sp2h = Proj2htmlForm(title="Save project as html pages",
                         subtitle=lbltxt)  #, subtitlepos='w')


class Proj2htmlForm(scrolledForm):
    " class to open a window to get user input "
    def makeButtons(self, bot):
        self.addButton(bot, text='OK', command=self.go, side='left')
        self.addButton(bot, text='Cancel', command=self.quit, side='right')
        
    def mkMainFrame(self):
        fr = self.fmain
        self.st = Pmw.ScrolledText(fr,
                                   labelpos='nw',
                                   label_text='Notes:',
                                   usehullsize = 1,
                                   hull_width = 600,
                                   hull_height = 250)
        self.st.component('text').configure(background='white')
        self.st.pack(side='top', padx=4, pady=4,expand=1, fill='both')

        # the Save as entry box
        filename = os.path.join(GB.P.projdir,GB.P.projfile + ".html")
        fr2 = Frame(fr)
        fr2.pack(expand=1, fill='both', padx=4, pady=4)
        self.ef = Pmw.EntryField(fr2, labelpos='nw', value=filename,
                                     label_text="Save project to file:")
        self.ef.pack(side='left', expand=1, fill='both',padx=5, pady=5)
        browse = Button(fr2,  text="Browse",
                        command=Command(getFile, self.ef,"*.html"))
        browse.pack(side='right', padx=5, pady=5)

    def go(self):
        filename = self.ef.get()
        notes = self.st.get()
        if filename == "":
            displayError("an output filename is required")
            return
        self.top.destroy()
        sph = saveProj2html(filename, notes)

# --------------------------------------------------------------------                    
class saveProj2html:
        
    def __init__(self, mainfile=None, notes=None):
        # create the main html file and html directory
        if mainfile == None:
            mainfile = os.path.join(GB.P.projdir,GB.P.projfile + ".html")
        try:
            fp = open(mainfile, 'w')
            fp.close()
        except:
            displayError("Unable to open %s for writing." % mainfile)
            return
        base, ext = os.path.splitext(mainfile)
        htmldir = base + "_files"
        mkdir = makeDirectory(htmldir)
        if not mkdir:
            displayError("Unable to create directory." % htmldir)
            return
        self.mainfile = mainfile
        self.htmldir = htmldir
        self.notes = notes

        self.make_main_page()

    def make_main_page(self):
        title = "Spire project: %s" % GB.P.title
        wintitle = GB.P.title
        mainfile = self.mainfile
        start_html(mainfile, title=title, wintitle=wintitle)
        # create the header at the top
        H = []
        id = GB.P.ID
        if id != None and id != "":
            H.append( ['ID: ', GB.P.ID] )
        H.append( ['title: ', GB.P.title] )
        H.append( ['project file: ', GB.P.projfile] )
        H.append( ['project directory: ', GB.P.projdir] )
        H.append( ['host: ', GB.P.host] )
        target = GB.P.config
        path, linktext = os.path.split(target)
        H.append( ['configuration: ', make_link(target, linktext)] )
        if hasattr(GB.P, 'startdate') and GB.P.startdate != "":
                H.append( ['date started: ', GB.P.startdate] )
        H.append( ['last updated: ', GB.P.updated] )
        H.append( ['data extension: ', GB.P.dataext] )
        if hasattr(GB.P, 'pixelsize') and GB.P.pixelsize != "":
            H.append( ['pixel size: ', trim_zeroes(GB.P.pixelsize)] )
        if hasattr(GB.P, 'kv') and GB.P.kv != "":
            H.append( ['electron energy: ', trim_zeroes(GB.P.kv)] )
        text = make_table(H, border=0, bgcolor="#FFFFFF")
        text.append("\n<p></p><hr><p></p>\n")
        append_text(mainfile, text)

        # add the notes section
        if self.notes.strip() != "":
            n = self.notes.replace("&", "&amp;")
            n = n.replace("<", "&lt;")
            n = n.replace(">", "&gt;")
            text = ["<b>Notes:</b><pre>"]
            text.append(n)
            text.append("\n</pre><p></p><hr><p></p>\n")
            append_text(mainfile, text)

        # make the list of batch runs
        T = GB.P.T
        keys = T.keys()
        keys.sort()
        blist = []
        for k in keys:
            br = T[k]   # each is a SpiderBatchRun class object
            bid = br.id
            bdir = br.dir
            bat = br.batfile
            bdate = br.time_start[0]
            btime = br.time_start[1]
            bpage = os.path.join(self.htmldir, bid + ".html")
            blink = make_link(target=bpage, text=bat)
            bfnums = br.filenumbers
            blist.append( [bdir, blink, bdate, btime, bfnums] )
            GB.outstream("writing %s" % bpage)
            self.make_bat_page(bid, bpage, bat)
        headers = ['directory', 'procedure', 'date', 'time', 'filenumbers']
        text = make_table(blist, bgcolor="#FFFFFF", headerlist=headers,
                          headercolor="#BBCCFF")
        append_text(mainfile, text)

        end_html(mainfile)
        GB.outstream("...finished writing project to html files.")

    def make_bat_page(self, id, filename, procedure):
        start_html(filename, title=procedure, wintitle=id)
        br = GB.DB.BatchRun(id)
        bdir = br.dir
        bdate = br.time_start[0]
        btime = br.time_start[1]
        bfnums = br.filenumbers
        bparms = br.parameters
        # create the header
        H = [('ID: ', id)]
        H.append( ('batch file: ', procedure) )
        H.append( ('directory: ', bdir) )
        H.append( ('date: ', bdate) )
        H.append( ('time: ', btime) )
        if bfnums != None and bfnums != "":
            H.append( ('file numbers: ', bfnums) )
        bp = stringify(bparms)
        if bp != None and bp != "":
            H.append( ['parameters:', bp] )
        text = make_table(H, border=0, bgcolor="#FFFFFF")
        append_text(filename, text)

        # make the text file of the procedure
        path, x = os.path.split(filename)
        textfile = os.path.join(path, procedure + ".html")
        btxt = ["<html>\n<body>\n<pre>\n"]
        btxt = btxt + br.text
        btxt.append("\n</pre>\n</body>\n</html>")
        fp = open(textfile,'w')
        fp.writelines(btxt)
        fp.close()
        linktext = "Text of %s" % procedure
        mmtxt = "<p></p>" + make_link(target=textfile, text=linktext) + "<p></p>"
        append_text(filename, [mmtxt])
        
        # make the table of output files
        append_text(filename, ["<p></p><b>Output files:</b>\n"])
        hdrs = ['file', 'type', 'size', 'date', 'time']
        outfiles = br.outfiles
        if len(outfiles) > 1:
            outfiles = outfiles[0] + outfiles[1]
        rowlist = []
        for f in outfiles:
            if len(f) < 5:
                print file
                continue
            fn = f[0]
            ft = f[1]
            fs = ""
            if ft == 'Document':
                fs = f[2][0]
            elif len(f[2]) == 2:
                fs = "%s, %s" % (f[2][0], f[2][1])
            elif len(f[2]) == 3:
                fs = "%s, %s, %s" % (f[2][0], f[2][1], f[2][2])
            fd = f[3]
            fti = f[4]
            rowlist.append( [fn,ft,fs,fd,fti] )

        text = make_table(rowlist, bgcolor="#FFFFFF", headerlist=hdrs,
                          headercolor="#BBCCFF")
        append_text(filename, text)
        end_html(filename)

    # ----- end class saveProj2html

def start_html(file, title=None, wintitle=None):
    if wintitle == None: wintitle = ""
    txt = ["<html>\n"]
    txt.append("<head><title>%s</title></head>\n" % wintitle)
    txt.append("<body>\n\n")
    if title != None:
        txt.append("<h2>%s</h2>\n<p></p>\n" % title)

    fp = open(file,'w')
    fp.writelines(txt)
    fp.close()
    
def make_table(rowlist, border=1, cellspacing=1, cellpadding=4, bgcolor=None,
               headerlist=None, headercolor=None):
    t = ["<p></p>\n"]
    s = '<table border="%s" ' % border
    s += 'cellspacing="%s" ' % cellspacing
    s += 'cellpadding="%s"' % cellpadding
    if bgcolor != None:
        s += ' bgcolor="%s"' % bgcolor
    s += '>\n'
    t.append(s)
    # headers, if any
    if headerlist != None:
        if headercolor == None:
            t.append("<tr>\n")
        else:
            t.append('<tr bgcolor="%s">\n' % headercolor)
        for item in headerlist:
            t.append("<th>%s</th>" % item)
        t.append("\n</tr>\n")
    # rows of the table
    for row in rowlist:
        t.append("<tr>\n")
        for item in row:
            t.append("<td>%s</td>" % item)
        t.append("\n</tr>\n")

    t.append("</table>\n<p></p>\n")
    return t

def make_link(target, text):
    return '<a href="%s">%s</a>' % (target, text)

def append_text(file, text):
    "text should be a list of lines, each ending with a newline"
    fp = open(file,'a')
    if type(text) == type(["list"]):
        fp.writelines(text)
    else:
        fp.writelines([text])
    fp.close()        

def end_html(file):
    fp = open(file,'a')
    fp.write("</body>\n</html>\n")
    fp.close()

