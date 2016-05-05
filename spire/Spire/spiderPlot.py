#! /usr/bin/env python
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
import tkMessageBox 
from tkFileDialog import asksaveasfilename, askopenfilename

import os
import string
import sys

import GG   # needed only for instance destruction

# see if Gnuplot is available
# This code is executed when the module is first imported.
try:
    import Gnuplot, Gnuplot.funcutils
except ImportError:
    pass

def hasGnuplot():
    try:
        f = Gnuplot.__version__
        return 1
    except:
        return 0

def Gnuplot_promo():
    txt = "Unable to import Gnuplot.py.\n"
    txt += "Gnuplot.py is the Python interface to gnuplot.\n"
    txt += "Gnuplot.py can be downloaded from:\nhttp://gnuplot-py.sourceforge.net"
    return txt

# ----------------------------------------------------------

class MyGnuplotPlot:
    # input datafiles in list form
    def __init__(self, master, args):

        self.w = Toplevel(master)
        self.w.title('Gnuplot')
        #self.setOptionDB()

        class Dummy: pass
        self.var = Dummy()    # declares var an instance of Class Dummy
                              # used by the Checkbutton widgets
        self.displaylist = []
        self.g = Gnuplot.Gnuplot()

        self.x = StringVar()
        self.x.set("")
        self.y = StringVar()
        self.y.set("")
        self.xrange = ""
        self.yrange = ""
        self.cols = StringVar()
        self.cols.set("1:3")
        
        for f in args:
            self.displaylist.append(f)

        cblist = ()
        sf = Pmw.ScrolledFrame(self.w)
        self.f2 = sf.interior()
        self.f2.configure(background='white')

        for item in self.displaylist:
            setattr(self.var, item, IntVar())
            c = Checkbutton(self.f2, text=item, anchor='w',
                            variable=getattr(self.var, item))
            c.select()
            cblist = cblist + (c,)
            c.bind('<ButtonRelease-1>', self.select)
            
        for item in cblist:
            item.pack(side='top', anchor='w')
            
        sf.pack(side='top', fill='both', expand=1, padx=5, pady=5)

        f3 = Frame(self.w, relief=RAISED, borderwidth=1)
        Label(f3, text="set x range:").grid(row=0, column=0, sticky=W)
        xentry = Entry(f3, width=16, textvariable=self.x)
        xentry.grid(row=0, column=1)
        xentry.bind('<Return>', self.select)

        Label(f3, text="set y range:").grid(row=1, column=0, sticky=W)
        yentry = Entry(f3, width=16, textvariable=self.y)
        yentry.grid(row=1, column=1)
        yentry.bind('<Return>', self.select)

        Label(f3, text="set columns:").grid(row=2, column=0, sticky=W)
        centry = Entry(f3, width=16, textvariable=self.cols)
        centry.grid(row=2, column=1)
        centry.bind('<Return>', self.select)

        f3.pack(side='top', fill='both', expand=1)

        f5 = Frame(self.w, relief=RAISED, borderwidth=1)
        Addbut = Button(f5, text='Add', command=self.add_data)
        Addbut.grid(row=0, column=0, padx=5, pady=5)
        Clearbut = Button(f5, text='Clear', command=self.clear)
        Clearbut.grid(row=0, column=1, padx=5, pady=5)
        Savebut = Button(f5, text='Save', command=self.save)
        Savebut.grid(row=0, column=2, padx=5, pady=5)
        Quitbut = Button(f5, text='Close', command=self.remove)
        Quitbut.grid(row=0, column=3, padx=5, pady=5)
        f5.pack(side='top', fill='both')

        self.select()  # graph the selected items

    def setOptionDB(self):
        self.w.option_add('*font', 'Arial 12')
        self.w.option_add('*Entry*background', 'white')
        self.w.option_add('*foreground', 'black')
        #self.w.option_add('*background', 'white')

    def current_list(self):
        vlist = []
        slist = []
        for item in self.displaylist:
            x = getattr(self.var, item)
            y = x.get()
            vlist.append(y)
            
        n = len(self.displaylist)
        for i in range(n):
            if vlist[i] != 0:
                f = string.split(self.displaylist[i])
                slist.append(f[0])
        slist.sort()
        colstr = self.validateColumns()
        self.cols.set(colstr)
        return slist

    def select(self,event=None):    # plots the current selected list
        slist = self.current_list()
        self.plotter(slist)

    def add_data(self):
        datafile = askopenfilename()
        cwd = os.getcwd() + "/"
        datafile = string.replace(datafile,cwd,"")
        self.add2list(datafile)

    def add2list(self,item):
        if item not in self.displaylist:
            self.displaylist.append(item)
            setattr(self.var, item, IntVar())
            c = Checkbutton(self.f2, text=item, anchor='w',
                            variable=getattr(self.var, item))
            c.select()
            c.bind('<ButtonRelease-1>', self.select)
            c.pack(side='top', anchor='w')
            self.select()
        else:
            tkMessageBox.showerror('Error', '%s is already in the list' % item)

    def clear(self):
        for item in self.displaylist:
            x = getattr(self.var, item)
            x.set(0)
        
    def save(self):
        self.xrange = self.validateRange('x')
        self.yrange = self.validateRange('y')
        slist = self.current_list()
        if len(slist) == 0: return
        plotstr = "plot '%s' using 1:3 title '%s' with lines" % (slist[0],slist[0])
        if len(slist) > 1:
            for item in slist[1:]:
                plotstr = plotstr + ",\\\n '%s' using 1:3 title '%s' with lines" % (item,item)

        fname = asksaveasfilename()
        if fname == "": return
        fp = open(fname, 'w')
        if self.xrange != "":
            fp.write(self.xrange + "\n")
        if self.yrange != "":
            fp.write(self.yrange + "\n")
        fp.write(plotstr + "\n")
        fp.close()         
        
    def checkRange(self,yrange):
        if string.find(yrange, ":") == -1: return -1
        V = string.split(yrange, ":")
        for item in V:
            if item != '':
                try:
                    string.atof(item)
                except ValueError, e:
                    return -1
        return 0
        
    def rangeError(self):
        tkMessageBox.showerror('Error', 'Entries must be of the form:\n\tLo:Hi\n where Lo and Hi are numbers')

    def validateColumns(self):
        colstr = self.cols.get()
        if colstr != "":
            if (self.checkRange(colstr) != 0):
                self.rangeError()
                return "1:3"
        if colstr == "": colstr = "1:3"
        return colstr
        
    def validateRange(self,xy):
        if xy == 'x':
            self.xrange = self.x.get()
            if self.xrange != "" and self.xrange != None:
                if self.xrange[0] == '[':
                    self.xrange = self.xrange[1:]
                if self.xrange[-1] == ']':
                    self.xrange = self.xrange[:-1]
                if (self.checkRange(self.xrange) != 0):
                    self.rangeError()
                    return ""
                self.xrange = "set xrange[%s]" % (self.xrange)
            return self.xrange
        elif xy == 'y':
            self.yrange = self.y.get()
            if self.yrange != "" and self.yrange != None:
                if self.yrange[0] == '[':
                    self.yrange = self.yrange[1:]
                if self.yrange[-1] == ']':
                    self.yrange = self.yrange[:-1]
                if (self.checkRange(self.yrange) != 0):
                    self.rangeError()
                    return ""
                self.yrange = "set yrange[%s]" % (self.yrange)
            return self.yrange

    def plotter(self,L):   
        if len(L) == 0:
            self.g('clear')
            return
        
        self.g('set data style lines')    
        
        self.xrange = self.validateRange('x')
        if self.xrange != "" and self.xrange != None:
            self.g(self.xrange)
        else:
            self.g('set autoscale x')

        self.yrange = self.validateRange('y')
        if self.yrange != "" and self.yrange != None:
            self.g(self.yrange)
        else:
            self.g('set autoscale y')
                
        colstr = self.validateColumns()
        
        plotstr = "plot '%s' using %s title '%s' with lines" % (L[0],colstr,L[0])
        if len(L) > 1:
            for item in L[1:]:
                plotstr = plotstr + ", '%s' using %s title '%s' with lines" % (item,colstr,item)
                
        self.g(plotstr)

    def lift(self):
        if self.w.winfo_exists():
            self.w.lift()
            
    def remove(self):
        self.w.destroy()
        self.g('exit')
        GG.gnuplot = None


#####################################################################
if __name__ == '__main__':
    
    root = Tk()
    root.withdraw()
    
    app = MyGnuplotPlot(root,[])  #['data/roo001.dat'])
    root.mainloop()
