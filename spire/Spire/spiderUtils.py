# $Id: spiderUtils.py,v 1.1 2012/07/03 14:21:59 leith Exp $
#
# functions called by many modules

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
import os,string,sys
import time, threading
import shelve, stat
import re
from fnmatch import fnmatchcase
from glob import glob
from commands import getoutput
from random import random
import GB,GG
# can't import spiderClasses

# Gets patterns like '<chars>' or '[text 2]'
# [\S ]+ = one or more nonwhitespace characters or spaces
# ^ = must be at beginning of line
# Better first strip off the comment.
#re_spiderSymbol = re.compile("^(\[[\S ]+\])|^(<[\S ]+>)")

def stringify(thing, sep=","):
    " convert a list's contents into a single string "
    if type(thing) == type(["list"]):  # ['a','b','c'] -> "a,b,c"
        s = ""
        for item in thing:
            s += sep + str(item)
        s = s[1:]
    else:
        s = str(thing)
    s = s.strip()
    return s

def listReplace(list, old, new):
    if old in list:
        i = list.index(old)
        list[i] = new
    return list

def trim_zeroes(n):
    " trim zeroes from end of floating point number"
    n = str(n)
    if n.find(".") > -1:
        while n[-1] == "0":
            n = n[:-1]
    if n[-1] == ".":
        n = n[:-1]
    return n

def isPython(file):
    fn, ext = os.path.splitext(file)
    if ext == '.py': return 1
    else: return 0
    
####################################################################
#
# File utilites
def getfilenumber(filename):
    "returns file number as a string with leading zeroes "
    filename = os.path.basename(filename)
    fname,ext = os.path.splitext(filename)

    numstr = ""
    f = list(fname)
    f.reverse()
    done = 0
    for ch in f:
        if not done:
            try:
                int(ch)
                numstr = ch + numstr
            except:
                if numstr != "":
                    done = 1
    return numstr

def name2template(filename, all=0):
    " given 'mic021.dat' --> returns mic***.dat "
    " by default, only replaces number nearest extension. all !=0 replaces all"
    if len(filename) == 0: return ""
    path, basename = os.path.split(filename)
    fname,ext = os.path.splitext(basename)

    newfn = ""
    f = list(fname)
    f.reverse()
    if all:
        for ch in f:
            try:
                int(ch)
                newch = '*'
            except:
                newch = ch
            newfn = newch + newfn
    else:
        found = 0
        for ch in f:
            if not found:
                try:
                    int(ch)
                    newch = '*'
                except:
                    newch = ch
                    if newfn and newfn[0] == '*':
                        found = 1
            else:
                newch = ch
            newfn = newch + newfn
    fname = os.path.join(path,newfn) + ext
    return fname

# template should have asterisks, num can be int or a numbered filename.
# Like makeSpiderFilename, but it can accept a filename instead of a number.
def template2filename(template, n=0):  #numfile=None, n=None):
    "replaces asterisks with number: (pic***.dat, doc003.dat) returns pic003.dat"
    if type(n) == type(1):
        pass
    elif type(n) == type("string"):
        n = filenumber(n)
    else:
        print "template2filename: unable to parse input"
        return ""
    nstars = template.count("*")
    if nstars == 0:
        return template
    if len(str(n)) > nstars:
        print "template2filename: **** Warning number larger than template"
    numstr = str(n).zfill(nstars)
    sts = "*" * nstars
    filename = template.replace(sts,numstr)
    return filename


def grep(thestring, fileglob, nocase=None):
    if os.name != 'posix':
        return ""
    if nocase:
        cmd = "grep -i %s %s" % (thestring, fileglob)
    else:
        cmd = "grep %s %s" % (thestring, fileglob)
    return getoutput(cmd)

# Given list ['usr1', 'carlos', 'hcc1'], returns "/usr1/carlos/hcc1"
# Like os.path.join, but takes a list as argument.
def makepath(list, absolute=None):
    if absolute != None:
        pstr = os.sep
    else:
        pstr = ""
    for item in list:
        pstr += item + os.sep
    return pstr[:-1]

# projdir:  '/usr1/carlos/hcc', from project being started on local host.
# searchdir: '/tmp_mnt/net/crete/usr1/carlos/hcc', what remote host sees.
# Reset the projdir to the longer version (and config file as well).
def remoteProjectPath(projdir, searchdir=None):
    #print "remoteProjectPath:projdir, searchdir: %s, %s" % (projdir, searchdir)
    if chdir(projdir):
        return 1
    else:
        if searchdir == None or searchdir == "":
            searchdir = os.getcwd()
        else:
            searchdir = os.path.abspath(searchdir)
        if projdir in searchdir:
            if chdir(searchdir):
                #print "setting project dir %s to %s" % (GB.P.projdir, searchdir)
                GB.P.projdir = searchdir
                # then fix config file
                config = os.path.basename(GB.P.config)
                #if os.path.exists():
                GB.P.config = config
                return 1
    return 0

# given the full path to a file, returns only the path and filename
# under the project directory (return filename if not in project dir)
def projFilename(filename):
    if filename == "": return filename
    if not hasProject: return filename
    projdir = GB.P.projdir
    filename = truepath(filename)

    projlist = projdir[1:].split(os.sep)  # convert path to list
    fplist = filename[1:].split(os.sep)

    projdirname = projlist[-1]   # project dirname is last element
    if projdirname not in fplist: return filename
    if projdirname == fplist[-1]: return filename

    a = fplist.index(projdirname)  # index of the projdir in the list

    below = makepath(fplist[a+1:])    # below the project directory
    above = makepath(fplist[:a+1], absolute=1)  # /usr3/crete/carlos/hcc
    if above in projdir:
        return below
    else:
        return filename

# returns directory path under the project directory.
# given '/usr3/carlos/hcc/Particles/good/ngood001.hcc'
# returns 'Particles/good'
def projpath(filepath):
    fp = projFilename(filepath)
    path, base = os.path.split(fp)
    if os.path.isdir(base):
        return fp
    else:
        return path

def truepath(filepath):
    filepath = os.path.expanduser(filepath)
    filepath = os.path.normpath(filepath)
    filepath = filepath.replace("/tmp_mnt","")
    return filepath

# pop off the first path element
def pathpop(path):
    " given  /usr1/carlos/hcc, returns (usr1, carlos/hcc)"
    p = path.split(os.sep)
    if p[0] == "":
        if len(p) < 2:
            return path
        head = p[1]
        new = p[2:]
    else:
        head = p[0]
        new = p[1:]
    if len(new) < 1:
        return path
    np = new[0]
    for d in new[1:]:
        np += os.sep + d
    return (head,np)

def newfilename(prefix, directory=None):
    " returns highest numbered filename (incremented by 1) with prefix "
    if directory == None:
        directory = os.getcwd()

    alist = os.listdir(directory)
    blist = []
    for filename in alist:
        if string.find(filename, prefix) == 0:
            blist.append(filename)
    if len(blist) == 0:
        return prefix + '001'

    max = i = 0
    nplaces = 1
    for filename in blist:
        f,ext = os.path.splitext(filename)
        length = len(f)
        n = 1
        while n < length:
            try:
                i = int(f[-n:])
                nplaces = len(f[-n:])
                n += 1
            except:
                break
        if i > max:
            max = i

    newname = prefix + string.zfill(max+1,nplaces) + ext
    return newname

def gethostname():
    return os.uname()[1]
    " use this function instead of os.environ['HOST'] "
    """
    host = ""
    for key in ["HOST", "HOSTNAME", "COMPUTERNAME"]:
        try:
            host = os.environ[key]
            return host
        except:
            pass
    return host
    """

# dir = a path, which is searched for /net/hostname/ .
# if dir == None just returns current host.
def getHost(dir=None):
    host = ""
    if dir == None:
        host = gethostname()
    else:
        if dir.find('/net/') > -1:
            d = dir.split('/')
            n = len(d)
            for i in range(n):
                if d[i] == 'net':
                    host = d[i+1]
                    break
    return host


#################################################################
#
# directory utilitiess

def getDirectories(dir):
    " return list of 1st level directories "
    chdir(dir)
    directories = []
    L = os.listdir(dir)
    for f in L:
        if os.path.isdir(f):
            directories.append(f)
    return directories
            
def fixDirname(directory):
    if type(directory) != type(""):
        directory = str(directory)
    directory = string.replace(directory,"/tmp_mnt","")
    return directory

def chdir(directory, verbose=1):
    directory = fixDirname(directory)

    try:
        os.chdir(directory)
        return 1
    except:
        # for the odd case where you're already in the requested dir
        #print "chdir: requested dir: %s" % os.path.abspath(directory)
        #print "chdir: this dir %s" % os.getcwd()
        if os.path.abspath(directory) == os.getcwd():
            return 1
        if verbose != 0:
            print 'Unable to access directory ' + directory + ' from ' + os.getcwd()
            #######GB.errstream(s)
        return 0

def dirsizeTooBig(directory):
    " checks directory size (using stat) against MAXDIRSIZE, returns 0 or 1 "
    directory = fixDirname(directory)
    maxsize = 17000  #GG.sysprefs.MaxDirsize
    tup = os.stat(directory)
    dirsize = tup[6]
    if dirsize > maxsize:
        return 1
    else:
        return 0

# gets rid of "/tmp_mnt" in path
def getCurrentDir():
    d = os.getcwd()
    if string.find(d, "/tmp_mnt") > -1:
        d = string.replace(d, "/tmp_mnt", "")
    return d

def makeDirectory(dir):
    if dir == "": return 1
    if os.path.exists(dir):
        if checkFileAccess(dir):
            return 1
        else:
            GB.errstream('Unable to access ' + dir + '\nYou must have read/write permission.')
            return 0
    try:
        os.mkdir(dir, 0775)
        return 1
    except OSError:
        GB.errstream('Unable to create ' + dir)
        return 0

def dirlist(directory, pattern=None):
    if pattern == None:
        return os.listdir(directory)
    olddir = os.getcwd()
    os.chdir(directory)
    flist = glob(pattern)
    os.chdir(olddir)
    return flist

# read a directory, return its contents in a list
# A directory is a list of 2 items: [name,[filelist]]
# d: dir to read. 
# ftypes : list of file types to include
SHOWHIDDEN = 0

def read_dirtree(d, filetypes=["*"], verbose=0):
    "returns a list: dirs = lists, files = strings"
    # try to change to the target directory
    cwd = os.path.basename(os.getcwd())
    if verbose:
        print "cwd: %s" % cwd
        print "d %s" % d
    if d != cwd:
        if not chdir(d):
            return
        else:
            if verbose: print "successfully changed to %s" % os.getcwd()
        
    dcontents = []
    ftypes = []
    if len(filetypes) == 1 and filetypes[0].find(",") > 0:
        # ie it's several comma-separated wildcards
        filetypes = filetypes[0].split(",")
    for ft in filetypes:
        ftypes.append(ft.strip())
    if verbose: print ftypes
                      
    dlist = os.listdir(os.getcwd())
    for item in dlist:
        if not SHOWHIDDEN and item[0] == ".":
            continue
        if os.path.isfile(item):
            match = 0
            for ft in ftypes:
                if fnmatchcase(item, ft):
                    match = 1
                    break
            if match:
                if item not in dcontents:
                    dcontents.append(item)
        elif os.path.isdir(item):
            if not dirsizeTooBig(item):
                if verbose: print "processing %s" % item
                dcontents.append(read_dirtree(item,ftypes))
                os.chdir("..")
            else:
                if verbose: print "skipping %s, too many files" % item
            
    return [os.path.basename(d), dcontents]

# a couple of function for dictionary list: Config.Dirs
def dirlist2dict(dirlist):
    " items in dirlist must be lists: [ dirname, [contentlist] ] "
    D = {}
    dir_order = [] # maintain order of directories
    for item in dirlist:
        if len(item) > 1:
            dirname = item[0]
            contents = item[1]
            if type(dirname) == type("string") and type(contents) == type(["list"]):
                D[dirname] = contents
                dir_order.append(dirname)
            else:
                print "dirlist2dict error: %s" % str(item)
    D['_dir_order'] = dir_order
    return D

def dict2dirlist(dict):
    if '_dir_order' in dict:
        keys = dict['_dir_order']
    else:
        keys = dict.keys()
    dirlist = []
    for k in keys:
        d = [k, dict[k]]
        dirlist.append(d)
    return dirlist

# return 1 if have R/W access, else 0
# First tries to change the access permissions.
# Works for directories too.
def checkFileAccess(f):
    # if it doesn't exist, see if it can be created (files only, not dirs)
    if not os.path.exists(f):
            try:
                fp = open(f, 'w')
                fp.close()
                return 1
            except:
                return 0
    if os.access(f,os.R_OK) and os.access(f,os.W_OK):
        return 1
    else:
        if os.path.isfile(f): mode = 0664
        elif os.path.isdir(f): mode = 0775
        else: return 0
        try:
            os.chmod(f,mode)
            return 1
        except:
            return 0

def delete(file):
    if os.path.exists(file):
        os.remove(file)

def savecopy(filename):
    savedcopy = "/tmp/" + os.path.basename(filename)
    delete(savedcopy)
    ret = os.system("cp %s %s" % (filename, savedcopy))
    if ret == 0:
        return savedcopy
    else:
        return ""
      
# checks if the string has a Spider symbolic variable,
# returns a tuple (symbol, value)
# For FR G lines, not assignments
def spiderSymbol(text):
    " returns tuple ('[symbol]', 'value')"
    txt = text.strip()
    symbol = ""
    value = ""
    if txt == "": return (symbol, value)

    for brackets in [ ("[","]"), ("<",">") ]:
        left, right = brackets

        if txt[0] == left:
            a = txt.find(right)
            if a:
                symbol = txt[:a+1]
                t = txt[a+1:]  # after the symbol
                c = t.find(';')
                if c > -1:
                    value = t[:c].strip()
                else:
                    value = t.strip()
    #if symbol[:5] == "[ang-":
    #   print "SYMBOL %s" % symbol
    #   print "VALUE %s" % value
    return (symbol, value)

def symbolValueComment(text):
    " returns tuple ('<symbol>', 'value', 'comment') includes ';'"
    symbol, value = spiderSymbol(text)
    comment = getComment(text)
    #if symbol[:5] == "[ang-":
    #   print "symbol %s" % symbol
    #   print "value %s" % value
    #   print "comment %s" % comment

    return (symbol,value,comment)

def stripComment(line, strip=1):
    " removes Spider comment, and end whitespace from remaining text "
    n = line.find(";")
    if n > -1:
        line = line[:n].rstrip()
        
    if strip:
        line = line.strip()
    return line

def getComment(line):
    comment = ""
    c = line.find(';')
    if c > -1:
        comment = line[c:].strip()
    return comment

def fileReadLines(filename):
    if filename.find("/tmp_mnt") > -1:
        filename = filename.replace("/tmp_mnt", "")
    try:
        fp = open(filename,'r')
        B = fp.readlines()
        fp.close()
        return B
    except IOError, e:
        txt = 'Unable to open file \n%s\n' % (filename)
        if e:
            txt = txt + str(e) + '\n'
        GB.errstream.write(txt)
        #GB.errstream.write('Unable to open file \n' + filename, e)
        return None
    
def fileWriteLines(filename, B):
    if filename.find("/tmp_mnt") > -1:
        filename = filename.replace("/tmp_mnt", "")
    try:
        fp = open(filename,'w')
        for item in B: fp.write(item)
        fp.close
        return 1
    except IOError, e:
        GB.errstream.write('Unable to write to file ' + filename + '\n' + e + '\n')
        return None

def docWriteLines(filename, data):
    if filename.find("/tmp_mnt") > -1:
        filename = filename.replace("/tmp_mnt", "")
    try:
        hdr = makeDocfileHeader(filename, batext='spi')
        fp = open(filename,'w')
        fp.write(hdr)
        key = 1
        for item in data:
            fp.write("%5d 1%12.3f\n" % (key, item))
            key = key + 1
        fp.close()
        return 1
    except IOError, e:
        GB.errstream.write('Unable to write to file\n' + str(e) + '\n')
        return None

def hasExtension(file, ext=None):
    if ext == None:
        if hasProject():
            ext = GB.P.dataext
        else:
            return 0
    if ext[0] != '.':
        ext = '.' + ext

    file, fext = os.path.splitext(file)   # fext has leading '.'
    if fext == ext:
        return 1
    else:
        return 0

# add extension, if it's not already there
# If file has another 3-letter extension, replace it.
def addExtension(file,ext=None):
    if ext == None:
        if hasProject():
            ext = GB.P.dataext
        else:
            return file
    if ext[0] != '.':
        ext = '.' + ext
        
    xfile, fext = os.path.splitext(file)   # fext has leading '.'
    if fext == ext:  # it's already there
        return file
    elif fext == "": # has no extension: add it
        return file + ext
    elif len(fext) == 4:  # has a 3-letter extension: replace it
        return xfile + ext
    else:    # extension is not a 3-letter Spider ext. Append new ext
        return file + ext

def FR_tag(s):
    " return 1st occurence of '<str>' or '[str]' strings"
    a = string.find(s,'<')
    if a > -1:
        b = string.find(s,'>')
        if b > -1 and b > a:
            return s[a:b+1]
    a = string.find(s,'[')
    if a > -1:
        b = string.find(s,']')
        if b > -1 and b > a:
            return s[a:b+1]
    return ""

def makeDocfileHeader(filename, batext=None):
    filename = os.path.basename(filename)
    fn, ext = os.path.splitext(filename)
    ext = string.replace(ext,".","")
    if batext == None:
        batext = ext
    date,time,idstr = nowisthetime()
    h = " ;%s/%s   %s AT %s   %s\n" % (batext,ext,date,time,filename)
    return h

def lastModified(filename):
    " returns time in no. seconds since the epoch "
    " if file doesn't exist, returns 0"
    if os.path.exists(filename):
        fp = open(filename,'r')
        s = os.fstat(fp.fileno())
        return s[stat.ST_MTIME]
    else:
        return 0
    
# READDOC
# returns a list of items from a column (0 is key, 1 is 1st data column)
# positionals: file, col; keywords= file, col%umn, start%key, end%key
# rewrite to use Numerical arrays
def readdoc(filename, col):
    if col > 0: col = col + 1

    B = fileReadLines(filename)
    if B == None: return []

    D = []
    for item in B:
        a = item[0:5]  # the first 6 chars
        if ';' in a:
            continue
        else:
            a = string.split(item)
            d = string.atof(a[col])
            D.append(d)
    return D

##################################################################
#
# Project utilities

def hasProject(attr=None):
    if not hasattr(GB,'P'): return 0
    if attr == None and hasattr(GB.P,'ID'): return 1
    if attr != None and hasattr(GB.P,attr): return 1
    return 0

def hasConfig(attr=None):
    if attr == None:
        if hasProject() and hasattr(GB,'C') and \
           hasattr(GB.C,'Dialogs') and len(GB.C.Dialogs) > 0:
            return 1
        else:
            return 0
    else:
        if hasProject() and hasattr(GB,'C') and hasattr(GB.C, attr):
            return 1
        else:
            return 0

def makeRunID(time_start):
    "input = tuple: (date,time), e.g., ('16-JAN-2004', '14:27:07')"
    " returns a string "
    #print "makeRunID: %s" % str(time_start)
    dt = string.split(time_start[0],'-')
    day = dt[0]
    y = dt[2]
    year = y[-2:]  # 2 digit year (for Y3K fun)
    m = dt[1]
    if m == 'JAN': mo = '01'
    elif m == 'FEB': mo = '02'
    elif m == 'MAR': mo = '03'
    elif m == 'APR': mo = '04'
    elif m == 'MAY': mo = '05'
    elif m == 'JUN': mo = '06'
    elif m == 'JUL': mo = '07'
    elif m == 'AUG': mo = '08'
    elif m == 'SEP': mo = '09'
    elif m == 'OCT': mo = '10'
    elif m == 'NOV': mo = '11'
    elif m == 'DEC': mo = '12'
    tm = string.split(time_start[1],':')
    hr = tm[0]
    min = tm[1]
    sec = tm[2]
    id = year + mo + day + hr + min + sec
    return id

# returns current time as tuple of 3 strings: (date, time, ID)
# e.g., ('16-OCT-03', '13:08:16', '031016130816')
def nowisthetime():
    tt = time.localtime(time.time())
    # localtime return format: (2003, 10, 16, 12, 48, 30, 3, 289, 1)
    t = string.split(time.asctime(tt))
    # asctime return format: 'Thu Oct 16 12:50:17 2003'
    mo = string.upper(t[1])
    day = t[2]
    if len(day) < 2: day = '0' + day
    timestr = t[3]
    yr = t[4]
    datestr = "%s-%s-%s" % (day, mo, yr)

    yr = yr[-2:]
    # this is just to get the month as a number
    d = map(str,tt)   # stringify all numbers in the tuple
    mon = d[1]
    if len(mon) < 2: mon = '0' + mon
    (h,m,s) = string.split(timestr,':')
    idstr = "%s%s%s%s%s%s" % (yr,mon,day,h,m,s)

    return (datestr, timestr, idstr)


def hasDatabase():
    " is GB.DB a Spider ProjectDatabase object"
    if hasattr(GB, 'DB') and hasattr(GB.DB, 'SpiderProjectDatabase'):
        return 1
    else:
        return 0
    
def projSave(verbose=0):
    if not hasProject() and verbose == 1:
        GB.errstream('No project to save')
        return

    t = nowisthetime()
    GB.P.updated = t[0] + ", " + t[1]
    if hasDatabase():
        GB.DB.put('Project', GB.P)
    else:
        return 0

    GB.outstream("\nProject: %s, ID: %s\n" % (GB.P.title,GB.P.ID))
    prjtxt = "%s saved " % (os.path.join(GB.P.projdir,GB.P.projfile))
    prjtxt = prjtxt + time.asctime(time.localtime(time.time()))
    GB.outstream(prjtxt + "\n")
    return 1
    #except:
    #    GB.errstream('Error in spiderUtils.projSave')
    #    return 0

def getBatchRun(id, outputs=None):
    """ returns zero if unsuccessful """
    " outputs = 1 : full-sized, ie, with output file list "
    if not hasProject(): return 0
    br = 0
    if not outputs:
        # first try the 'lite' in-core project file, GB.P.T
        if hasattr(GB.P,'T') and GB.P.T.has_key(id):
            br = GB.P.T[id]
        else:
            # get full-sized batch run from database, but return w/o outputs
            if hasattr(GB, 'DB'):
                br = GB.DB.BatchRun(id)
                if br != 0:
                    br.outfiles = []
                    br.text = ""
    else:
        if hasattr(GB, 'DB'):
            br = GB.DB.BatchRun(id)
    return br

def saveBatchRun(batchrun):
    " Saves batch run to project, appends id to RunList. saveBatchRun will"
    " increment id if it's already in RunList. Returns batch id "
    if not hasProject(): return

    id = str(batchrun.id)  # even though batchrun.id should already be a string

    if id in GB.P.RunList:
        #GB.outstream("%s %s IS ALREADY in RunList\n" % (id, batchrun.batfile))
        while id in GB.P.RunList:
            id = str(int(id) + 1)
            if len(id) < 12:
                id = '0' + id  # cos loses leading zero in str/int conversion
        batchrun.id = id
    else:
        pass
        #GB.outstream("%s %s not in RunList\n" % (id, batchrun.batfile))
        
    GB.P.RunList.append(id)
    GB.DB.addBatchRun(batchrun) # put it in the project file

    # put a simpler version in the project table
    batchrun.outfiles = []
    batchrun.text = ""
    GB.P.T[id] = batchrun

    # check if project viewer window is displayed
    if hasattr(GB,'projview') and hasattr(GB.projview, 'addBatchRun'):
        GB.projview.addBatchRun(batchrun)

    return batchrun.id

def deleteBatchRun(id):
    if not hasProject(): return
        
    if id in GB.P.RunList:
        i = GB.P.RunList.index(id)
        del GB.P.RunList[i]      # delete from RunList
        
    GB.DB.delBatchRun(id)     # delete from the project file
    
    if GB.P.T.has_key(id):
        del GB.P.T[id]           # delete from project

####################################################################
# threading utilities

def isMainThread():
    thred = threading.currentThread().getName()
    if thred == GG.spidui.threadname:
        return 1
    else:
        return 0

def threadedGUIcall(function=None):
    " writes thread package to GB.ThreadDictionary, calls MainGUI, "
    " waits for call to finish, reads result from GB.ThreadDictionary[package]"
    this_thread = threading.currentThread()
    if not hasattr(this_thread, 'package'):
        print "threadedGUIcall: no thread package found"
        return
    
    name = this_thread.package.name
    module, func, kwargs = getCallerInfo(function)
    #print "threadedGUIcall: %s, %s %s" % (module, func, str(kwargs))
    this_thread.package.func   = func
    this_thread.package.kwargs = kwargs
    this_thread.package.module = module
    
    e = threading.Event()
    this_thread.package.flag = e
    GB.ThreadDictionary[name] = this_thread.package

    #print "threadedGUIcall: calling write_queue"
    
    GG.spidui.write_queue(name)  # request Main Gui to call function
    
    this_thread.waitevent = e  # in thread object, not package, for stopping
    e.wait()
    #print "threadedGUIcall:done waiting"
    
    # check if e was set by requested function or by join()
    if this_thread._stopevent.isSet():
        return
    # else, get the package from the global dictionary & check output
    package = GB.ThreadDictionary[name]
    if hasattr(package, 'output'):
        result = package.output

    return result

"""
getCallerInfo():
Each item in framelist is a tuple with frameobject as 1st item:
(<frame object at 0x1040c2e8>, '/tmp_mnt/home/carlos/rec/Spire/myfunc.py', 13,
'thisfunc', ['    getFuncAndKwargs()\n'], 0)
"""
from inspect import currentframe, getouterframes, getargvalues

def getCallerInfo(function=None):
    " input is a string"
    "returns (module, function, kwargs), which are (string, string, dictionary)"
    framelist = getouterframes(currentframe())
    
    frameno = 0
    if function != None:
        # if given function, use function to find the frame number
        for fr_obj in framelist:
            if fr_obj[3] == function:
                break
            frameno += 1
    else:
        # if no function name supplied, go thru framelist 
        thisfunc = "getCallerInfo"
        ignorefunc = "threadedGUIcall"
                
        for fr_obj in framelist:
            func = fr_obj[3]
            #print "getcallerinfo function: %d %s" % (frameno, func)
            if func == thisfunc or func == ignorefunc:
                frameno += 1
                continue
            else:
                function = func
                break

    frame = framelist[frameno][0]
    modulepath = framelist[frameno][1] # e.g., '/home/carlos/rec/Spire/myfunc.py'
    module = os.path.split(modulepath)[-1]
    module = module.replace('.py',"")
    
    av = getargvalues(frame)   # av = (args,varargs,varkw,locals) where
    #                            locals is dictionary of local values
    args = av[0]
    kw = av[3]  # which may contain more than the args
    kwargs= {}
    for arg in args:
        if kw.has_key(arg):
            kwargs[arg] = kw[arg]

    return (module, function, kwargs)

#$$$$$$$$$$$ NOT SURE IF NEXT 2 ARE USED ANYMORE

class cmdThread(threading.Thread):
    def __init__(self, cmd):
        self.cmd = cmd
        self._stopevent = threading.Event()
        threading.Thread.__init__(self)
        
    def run(self):
        os.system(self.cmd)

    def join(self):
        self._stopevent.set()
        threading.Thread.join(self)
    
def threadCommand(cmd):
    "uses a thread to run a command and returns immediately"
    tc = cmdThread(cmd)
    tc.start()
    
####################################################################
# Execution utilities

def executeCommand(prog, args=None):
    " run an external program with its arguments "
    if args == None:
        args = []
    cmd = prog
    
    # add '-persist' for gnuplot
    path, tail = os.path.split(prog)
    if tail == 'gnuplot' and '-persist' not in args:
        args = ['-persist'] + args
        
    for arg in args:
        cmd += " %s" % arg
    print cmd
    os.system(cmd)

# see "9.1 Avoiding lambda in callbacks", Python Cookbook
class Command:
    def __init__(self, callback, *args, **kwargs):
        self.callback = callback
        self.args = args
        self.kwargs = kwargs
    def __call__(self):
        return apply(self.callback, self.args, self.kwargs)
  
import popen2, fcntl, select

def makeNonBlocking(fd):
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    try:
      fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NDELAY)
    except AttributeError:
      fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.FNDELAY)

def getCommandOutput(command):
    child = popen2.Popen3(command, 1) # Capture stdout and stderr from command
    child.tochild.close()             # don't need to write to child's stdin
    outfile = child.fromchild
    outfd = outfile.fileno()
    errfile = child.childerr
    errfd = errfile.fileno()
    makeNonBlocking(outfd)            # Don't deadlock! Make fd's nonblocking.
    makeNonBlocking(errfd)
    outdata = errdata = ''
    outeof = erreof = 0
    while 1:
        ready = select.select([outfd,errfd],[],[]) # Wait for input
        if outfd in ready[0]:
            outchunk = outfile.read()
            if outchunk == '': outeof = 1
            outdata = outdata + outchunk
        if errfd in ready[0]:
            errchunk = errfile.read()
            if errchunk == '': erreof = 1
            errdata = errdata + errchunk
        if outeof and erreof: break
        select.select([],[],[],.1) # Allow a little time for buffers to fill
    err = child.wait()
    #if err != 0:
        #raise RuntimeError, '%s failed with exit code %d\n%s' % (
            #command, err, errdata)
    return outdata, errdata

def getCommandOutput2(command):
    child = os.popen(command)
    data = child.read()
    err = child.close()
    if err:
        raise RuntimeError, '%s failed with exit code %d' % (command, err)
    return data

# for ON/OFF flags: sets 'false', 'off' to 0,
# Nonzero values are set to 1.
# use: arg = isTrue(arg)
def isTrue(arg):
    arg = str(arg)
    if arg == "0": return 0
    uarg = string.upper(arg)
    if uarg == "OFF": return 0
    if uarg == "FALSE" or uarg == "F": return 0
    return 1

# appends tmpresult to results file, then deletes tmpresult
def closeResults(resultsname, tmpname, tmpfp):
    tmpfp.close()                # close tmpresult file
    if not os.path.exists(resultsname):
        return -1
    if not os.path.exists(tmpname):
        return -1
    fpres = open(resultsname,'a')   # open for appending
    fptmp = open(tmpname,'r')
    GB.outstream('Closing results file ....')
    fpres.writelines(fptmp.readlines())  # transfer tmpres to results
    fptmp.close()
    fpres.close()
    delete(tmpname)
    return 1

def results2spireout(resultsfile):
    spireout = resultsfile.replace('results', GG.sysprefs.spireout)
    return spireout

####################################################################
# 
# text processing utilities

def uniqueFilename(prefix=None, extension=None, length=0):
    " generate a random filename "
    uniq = ""
    # prefix
    if prefix == None: # then generate a 2-letter prefix
        uniq += string.lowercase[int(26*random())]
        uniq += string.lowercase[int(26*random())]
    else:
        uniq = prefix

    fill = 0

    if extension:
        if extension[0] != '.':
            extension = '.' + extension
        if length != 0:
            fill = length - (len(uniq) + len(extension))
        if fill < 1:
            fill = 5
    elif not extension:
        extension = ""
        if length != 0:
            fill = length - len(uniq)
        if fill < 1:
            fill = 6
            
    if fill > 16: fill = 16
            
    r = str(random())
    r = r[2:]  # get rid of leading "0."
    if fill > len(r):
        fill = len(r)

    uniq += r[:fill] + extension

    while os.path.exists(uniq):
        print "%s already exists, generating another name" % uniq
        uniq = uniqueFilename(prefix=prefix, extension=extension, length=length)
    return uniq

# newFileSymbol: returns line with new filename after the symbol.
# no errors msgs. if error, just returns old line.
def newFileSymbol(oldline, newfilename):
    """ replace path in '<symbol>path ; comment'  """
    if string.find(oldline,";") < 0:
        return oldline
    c = string.split(oldline,';')
    code = c[0]
    comment = c[1]
    
    a = string.find(code,'>')
    if a < 0:
        a = string.find(code,']')
    if a < 0:
        return oldline  # couldn't find symbolic variable
    symbol = code[:a+1]

    return symbol + newfilename + "    ; " + comment

# ------------------------------------------------------------
# if it's a proper batch file, returns lines in the batch header,
# else returns empty list
# Input : list of lines read by fileReadLines
# Returns: lines up & including 'end batch header' statment
#          if 'end' not found, returns empty list
def batHeader(B):
    H = []
    found = 0
    for line in B:
        H.append(line)
        if string.find(line,GB.end_of_header) > -1:
            found = 1
            break
    if not found:
        GB.errstream.write('missing END BATCH HEADER line\n')
    return H

