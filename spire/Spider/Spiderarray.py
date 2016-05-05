# Spider Python Library: Spiderarray.py
# Copyright (C) 2006,2010  Health Research Inc.
#
# HEALTH RESEARCH INCORPORATED (HRI),
# ONE UNIVERSITY PLACE, RENSSELAER, NY 12144-3455
#
# Email:  spider@wadsworth.org
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.

import sys, struct

try:
    import numpy
    _HAS_NUMPY_ = 1
except:
    try:
        import Numeric
        _HAS_NUMPY_ = 0
    except:
        print "SpiderArray requires the NumPy scientific library for Python"
        sys.exit()
        
from Spider.Spiderutils import getSpiderHeader, SpiderHeaderClass, makeSpiderHeader

def spider2array(filename, dtype='float32'):
    hdr = getSpiderHeader(filename)
    hc = SpiderHeaderClass(hdr) # a class that simplifies accessing header elements 
    hdrbytes = int(hc.labbyt)

    iform = int(hc.iform)
    if iform == 1:
        isVolume = 0
    elif iform == 3:
        isVolume = 1   # to do: support for Fourier iforms
    else:
        print "iform %d not supported" % iform
        return None

    xsize = int(hc.nsam)
    ysize = int(hc.nrow)
    if isVolume:
        zsize = int(hc.nslice)
        datawords = xsize * ysize * zsize
    else:
        datawords = xsize * ysize
    databytes = datawords * 4
    
    # seek ahead to the data
    fp = open(filename,'rb')
    fp.seek(hdrbytes)
    f = fp.read(databytes)
    fp.close()

    if int(hc.bigendian):
        fmt = '>%df' % datawords
    else:
        fmt = '<%df' % datawords

    t = struct.unpack(fmt,f)

    if _HAS_NUMPY_:
        arr = numpy.asarray(t, dtype=dtype)
    else:
        arr = Numeric.array(t, savespace=1)
        # the Numeric savespace flag keeps the data at 32 bits (o.w. -> 64 bits)

    if isVolume:
        arr.shape = zsize, ysize, xsize
    else:
        arr.shape = ysize, xsize
    return arr


def array2spider(arr, filename):
    # create and write the SPIDER header
    dims = arr.shape
    if len(dims) == 1:
        dims = (dims[0],1)
    hdr = makeSpiderHeader(dims)
    if len(hdr) < 256:
        raise IOError, "Error creating Spider header"
    try:
        fp = open(filename, 'wb')
        fp.writelines(hdr)
    except:
        raise IOError, "Unable to open %s for writing" % filename

    # write image data
    if _HAS_NUMPY_:
        if arr.dtype == 'float32':
            fp.write(arr.tostring())
        else:
            farr = arr.astype(numpy.float32)
            fp.write(farr.tostring())
    else:
        # older Numeric code
        if arr.typecode() == Numeric.Float32:
            fp.write(arr.tostring())
        else:
            farr = arr.astype(Numeric.Float32)
            fp.write(farr.tostring())
    fp.close

# The Image-to-Numeric functions were written by Fredrik Lundh.
# The numpy lines are from http://effbot.org/zone/pil-changes-116.htm
# but they require Image-1.1.6b2
import Image

def image2array(im):
    if _HAS_NUMPY_:
        a = numpy.asarray(im)  # a is readonly
    else:
        # older Numeric code
        if im.mode not in ("L", "F"):
            raise ValueError, "can only convert single-layer images"
        if im.mode == "L":
            a = Numeric.fromstring(im.tostring(), Numeric.UnsignedInt8)
        else:
            a = Numeric.fromstring(im.tostring(), Numeric.Float32)
        a.shape = im.size[1], im.size[0]
    return a

def array2image(a):
    if _HAS_NUMPY_:
        i = Image.fromarray(a)
        return i
    else:
        if a.typecode() == Numeric.UnsignedInt8:
            mode = "L"
        elif a.typecode() == Numeric.Float32:
            mode = "F"
        else:
            raise ValueError, "unsupported image mode"
        return Image.fromstring(mode, (a.shape[1], a.shape[0]), a.tostring())

# --------------------------------------------------------------------
if __name__ == '__main__':

    if len(sys.argv[1:]) < 1:
        print "Usage: python Spiderarray.py spiderfile"
        sys.exit()

    filename = sys.argv[1]
    arr = spider2array(filename)  # create a numpy array from a SPIDER image

    #if _HAS_NUMPY_:
    #   print arr.shape
    #   print arr.dtype

    b = arr * -1    # perform some arbitrary operation on the array

    newimg = 'new001.dat'

    array2spider(b, newimg) # write a numpy array out to a SPIDER image
    print "output written to " + newimg
