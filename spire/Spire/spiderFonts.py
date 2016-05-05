# $Id: spiderFonts.py,v 1.1 2012/07/03 14:21:59 leith Exp $
#
# various fonts used by Spire

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

class FontWindow:

    def __init__(self,master):
        self.master = master
        if GG.prefs.balloonHelp:
            self.balloon = GG.balloon
        
        " get the list of fonts "
        tmpList = tkFont.families()
        fontList=[]
        for item in tmpList:
            if item in ['nil','space'] or string.find(item,'glyph') > 0:
                pass
            elif string.find(item,'dingbats') > 0:
                pass
            else:
                fontList.append(item)
        fontList.sort()
        width = 0
        for item in fontList:
            w = len(item)
            if w > width: width = w

        " set up callbacks for String variables "
        self.current = GG.prefs.font    #SysFonts()
        self.spidFontVar = StringVar()
        self.spidFontVar.trace_variable("w", self.selectFont)

        " radiobuttons for 4 SPIRE fonts "
        fr = Frame(master)
        group = Pmw.Group(fr, tag_text='SPIRE fonts: ')
        gr = group.interior()
 
        rbsmall = Radiobutton(gr, text='', value='small', variable=self.spidFontVar)
        rbmed   = Radiobutton(gr, text='', value='medium',variable=self.spidFontVar)
        rbbig   = Radiobutton(gr, text='', value='large',variable=self.spidFontVar)
        rbout   = Radiobutton(gr, text='', value='output',variable=self.spidFontVar)

        lbsmall = Label(gr, text='Small', font=self.current.font['small'])
        lbmed   = Label(gr, text='Main (medium)', font=self.current.font['medium'])
        lbbig   = Label(gr, text='Labels (large)', font=self.current.font['large'])
        lbout   = Label(gr, text='SPIDER output', font=self.current.font['output'])
        rbsmall.grid(row=0,column=0, pady=5)
        rbmed.grid(row=1,column=0, pady=5)
        rbbig.grid(row=2,column=0, pady=5)
        rbout.grid(row=3,column=0, pady=5)
        lbsmall.grid(row=0,column=1, sticky='w')
        lbmed.grid(row=1,column=1, sticky='w')
        lbbig.grid(row=2,column=1, sticky='w')
        lbout.grid(row=3,column=1, sticky='w')
        self.LB = {'small':lbsmall,'medium':lbmed,'large':lbbig,'output':lbout}
        gr.pack(side='top',fill='both', expand=1, padx=5, pady=5)
        group.grid(row=0,column=0, padx=5, pady=5)

        " the 3 option menus for font, size, bold "
        fr2 = Frame(fr)

        initialFont = 'medium'

        self.fontVar = StringVar()
        self.fontVar.set(GG.spid.font[initialFont][0])
        self.fontVar.trace_variable("w", self.testFont)
        fontMenu = OptionMenu(fr2, self.fontVar, *fontList)
        fontMenu.configure(width=width)
        if GG.prefs.balloonHelp:
            self.balloon.bind(fontMenu,'choose a font for\nthe selected SPIRE font')
        fontMenu.pack(side='top',padx=5,pady=5)

        self.sizeVar = StringVar()
        self.sizeVar.set(GG.spid.font[initialFont][1])
        self.sizeVar.trace_variable("w", self.testFont)
        sizeList = [6,7,8,9,10,11,12,13,14,15,16,18,20,22,24,28,32,36,40,44,48]
        sizeMenu = OptionMenu(fr2,self.sizeVar, *sizeList)
        if GG.prefs.balloonHelp:
            self.balloon.bind(sizeMenu,'font size')
        sizeMenu.pack(side='top',padx=5,pady=5)
   
        self.boldVar = StringVar()
        self.boldVar.set(GG.spid.font[initialFont][2])
        self.boldVar.trace_variable("w",self.testFont)
        boldList = ['normal', 'bold']
        boldMenu = OptionMenu(fr2, self.boldVar, *boldList)
        if GG.prefs.balloonHelp:
            self.balloon.bind(boldMenu,'font style can be\nbold or normal')
        boldMenu.pack(side='top',padx=5,pady=5)
        fr2.grid(row=0,column=1, padx=5, pady=5)
     
        self.spidFontVar.set(initialFont)        

        frbut = Frame(fr, relief=GG.frelief)
        reset = Button(frbut, text='Reset', command=self.reset)
        if GG.prefs.balloonHelp:
            self.balloon.bind(reset,'Reset to values in %s' % GG.interface.file)
        reset.pack(side='left', padx=5, pady=5)
        save = Button(frbut, text='Save', command=self.save)
        if GG.prefs.balloonHelp:
            self.balloon.bind(save,'Save values to %s' % GG.interface.file)
        save.pack(side='left', padx=5, pady=5)
        sysdef = Button(frbut, text='Defaults', command=self.systemdef)
        if GG.prefs.balloonHelp:
            self.balloon.bind(sysdef,'Reset to system defaults')
        sysdef.pack(side='left', padx=5, pady=5)
        frbut.grid(row=1,column=0,columnspan=2, sticky='nsew')
        fr.pack(side='top', fill='both', expand=1)

    def selectFont(self, varName, *args):
        spidfont = self.spidFontVar.get()
        currentFont = self.current.font[spidfont]
        self.fontVar.set(currentFont[0])
        self.sizeVar.set(str(currentFont[1]))
        self.boldVar.set(currentFont[2])

    def testFont(self, varName, *args):
        spidfont = self.spidFontVar.get()  # small | medium | large | output
        label = self.LB[spidfont]   # which label to reconfigure
        # get the specified font values
        newfont = (self.fontVar.get(),self.sizeVar.get(),self.boldVar.get())
        label.configure(font=newfont)
        self.current.setFont(spidfont,newfont)

    def redraw(self):
        for spidfont in ['small', 'medium', 'large', 'output']:
            newfont = self.current.font[spidfont]
            label = self.LB[spidfont]
            label.configure(font=newfont)
            self.current.setFont(spidfont,newfont)
            
    def save(self):
        " write to $HOME/.spire "
        GG.spid = self.current   # set the new font values
        GG.interface.user.font = self.current
        writeUserPrefs()

    def reset(self):
        " read $HOME/.spire "
        readUserPrefs()
        GG.spidui.setOptionDB(widget=GG.topwindow)
        self.current = GG.spid
        self.redraw()

    def systemdef(self):
        " reset to system defaults "
        GG.interface.user.font = GG.SysFonts()
        GG.prefs = GG.interface.user
        GG.spid = GG.interface.user.font
        self.current = GG.spid
        GG.spidui.setOptionDB(widget=GG.topwindow)
        self.redraw()
        
if __name__ == "__main__":

    root = Tk()

    #root.option_add('*font', sf.font['medium'])

    f = FontWindow(root)
    root.mainloop()
