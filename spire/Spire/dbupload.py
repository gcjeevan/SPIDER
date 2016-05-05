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
import string,sys
from commands import getoutput

from Tkinter import *
import Pmw
import GB, GG
import spiderUtils
import spiderGUtils

"""
Each entry is of the form ["db entity name","value", "label"]
"""

values = [ ['Resolution','0.0','Resolution']
           ]

text_files = [ ['order_file', 'Power_Spectra/order_defgrps', 'Order File'],
               ['order_defocus','Power_Spectra/order_defgrps',	'Order_Defocus'],
               ['order_select', 'Refinement/order_select', 'Order_Select'],
               ['ctfs', 'Power_Spectra/def_avg', 'CTFS'],
               ['Final_Resolution_Curve', 'curve.jpg', 'Resolution curve'],
               ['Volume', 'final/bpr**', 'Volume']
                 ]

class db_upload:

    def __init__(self, master):

        p = 4

        f1 = Frame(master, borderwidth=2, relief='ridge')
        f1.pack(side='top', fill='x', expand=1)
        v = values[0]
        
        dbname = v[0]
        value = v[1]
        label = v[2]
        
        resVar = StringVar()
        resVar.set(value)
        
        dblabel = Label(f1, text=dbname)
        valabel = Label(f1, text=label)
        vaentry = Entry(f1, textvariable=resVar)
        
        dblabel.grid(row=0, column=0, padx=p, pady=p)
        valabel.grid(row=0, column=1, padx=p, pady=p)
        vaentry.grid(row=0, column=2, padx=p, pady=p)

        var1 = StringVar()
        var2 = StringVar()
        var3 = StringVar()
        var4 = StringVar()
        var5 = StringVar()
        var6 = StringVar()
        var7 = StringVar()
        vars = [var1,var2,var3,var4,var5,var6,var7]

        # text files
        row = 1
        for file in text_files:
            f = file
            dbname = f[0]
            value = f[1]
            label = f[2]

            var = vars[row-1]
            var.set(value)
            
            dblabel = Label(f1, text=dbname)
            valabel = Button(f1, text=label)
            vaentry = Entry(f1, textvariable=var, width=30)
            dblabel.grid(row=row, column=0, padx=p, pady=p, sticky='ew')
            valabel.grid(row=row, column=1, padx=p, pady=p, sticky='ew')
            vaentry.grid(row=row, column=2, padx=p, pady=p, sticky='ew')

            row = row + 1
        
        
        
def startwin():
    w = Toplevel(GG.topwindow)
    dbu = db_upload(master=w)
