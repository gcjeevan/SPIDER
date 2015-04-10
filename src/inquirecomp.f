
C++*********************************************************************
C
C  INQUIRECOMP.F   -- CREATED              APRIL 22 2013  ARDEAN LEITH
C
C **********************************************************************
C=*                                                                    *
C=* This file is part of:   SPIDER - Modular Image Processing System.  *
C=* SPIDER System Authors:  Joachim Frank & ArDean Leith               *
C=* Copyright 1985-2013  Health Research Inc.,                         *
C=* Riverview Center, 150 Broadway, Suite 560, Menands, NY 12204.      *
C=* Email: spider@wadsworth.org                                        *
C=*                                                                    *
C=* SPIDER is free software; you can redistribute it and/or            *
C=* modify it under the terms of the GNU General Public License as     *
C=* published by the Free Software Foundation; either version 2 of the *
C=* License, or (at your option) any later version.                    *
C=*                                                                    *
C=* SPIDER is distributed in the hope that it will be useful,          *
C=* but WITHOUT ANY WARRANTY; without even the implied warranty of     *
C=* merchantability or fitness for a particular purpose.  See the GNU  *
C=* General Public License for more details.                           *
C=* You should have received a copy of the GNU General Public License  *
C=* along with this program. If not, see <http://www.gnu.org/licenses> *
C=*                                                                    *
C **********************************************************************
C
C  INQUIRECOMP(ICOMP)
C
C  PURPOSE:  INQUIRE ABOUT COMPILER USED FOR THIS EXECUTABLE
C            I HAVE BEEN UNABLE TO FIND A PGI DEFINED VARIABLE!!al
C
C23456789 123456789 123456789 123456789 123456789 123456789 123456789 12
C--*********************************************************************

       SUBROUTINE INQUIRECOMP(ICOMP)

       IMPLICIT NONE
       INCLUDE 'CMBLOCK.INC'

       INTEGER               :: ICOMP

       INTEGER               :: IRTFLG

       ICOMP = -1

#if defined ( __GFORTRAN__ )  
       WRITE(NOUT,*) ' HAS DEFINED: __GFORTRAN__'
       WRITE(NOUT,*) ' COMPILED WITH: GFORTRAN'
       ICOMP = 1
#else
#if defined( SP_GFORTRAN )
       WRITE(NOUT,*) ' HAS DEFINED: SP_GFORTRAN'
       WRITE(NOUT,*) ' COMPILED WITH: GFORTRAN'
       ICOMP = 1
#else
#if defined( SP_IFC )
       WRITE(NOUT,*) ' HAS DEFINED: SP_IFC'
       WRITE(NOUT,*) ' COMPILED WITH: INTEL FORTRAN COMPILER'
       ICOMP = 2
#else
#if defined( __INTEL_COMPILER )      
       WRITE(NOUT,*) ' HAS DEFINED: __INTEL_COMPILER'
       WRITE(NOUT,*) ' COMPILED WITH: INTEL FORTRAN COMPILER'
       ICOMP = 2
#else
       WRITE(NOUT,*) ' COMPILED WITH: PGFORTRAN COMPILER'
       ICOMP = 0
#endif
#endif
#endif
#endif

       CALL REG_SET_NSEL(1,1,FLOAT(ICOMP),0.0,0.0,0.0,0.0,IRTFLG)
 
       END