# GLOBAL VARIABLES - NONGUI
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

import os,sys

DB = ""  # database object

spdout = 'spdout'
spderr = 'spderr'
remotecmd = 'rsh'   # rsh | ssh
shellcmd = 'csh'    # sh | csh
netexec = "remote"    # local | remote
user = os.environ["USER"]
checkPriorRun = 0
MaxNoFiles = 10
#saveResults = 1
#MaxResultLines = 100
end_of_header = "END BATCH HEADER"
project_dir_title = "project directory"  # how top-level directry appearsin menus
extDatabase = 1 # if set to 1, spidui will try to establish connection

VBOFF_var = ""
ThreadDictionary = {}  # will contain {name: package} pairs

##############################################################
# classes used by Spider projects

# output streams - must be set by functions that use them
outstream = ""
errstream = ""

# stdout and stderr for nongui methods (GUI uses msgbox)
class Output:
    def __init__(self):
        self.text = ''
    def __call__(self, string):
        self.write(string+'\n')
    def write(self, string):
        print string
    def writelines(self, lines):
        for line in lines: self.write(line)

""" Menus: directories and batch files for menus """
M = { 'dirlist' : [] }

# default parameter dictionary - labels are used in form
DP = {1 :[1,0,'zip flag',['do not unzip', 'unzip'] ],
      2 :[2,0,'file format', ['SPIDER','HiScan', 'Perkin Elmer','ZI scanner','Optronix']],
      3 :[3,0,'width (pixels)'],
      4 :[4,0,'height (pixels)'],
      5 :[5,0,'pixel size (A)'],
      6 :[6,0,'electron energy (kV)'],
      7 :[7,2.0,'spherical aberration (mm)'],
      8 :[8,0.0,'source size (1/A)'],
      9 :[9,0.0,'defocus spread (A)'],
      10:[10,0.0,'astigmatism (A)'],
      11:[11,0,'azimuth (degrees)'],
      12:[12,0.1,'amplitude contrast ratio (0..1)'] ,
      13:[13,10000,'Gaussian envelope halfwidth (1/A)'],
      14:[14,0,'lambda'],
      15:[15,0,'max. spatial frequency'],
      16:[16,1,'decimation factor'],
      17:[17,0,'window size (pixels)'],
      18:[18,0,'particle size (pixels)'],
      19:[19,0,'magnification'],
      20:[20,0,'scanning resolution (in microns:7,14,etc)'] }

