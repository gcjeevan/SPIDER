
C **********************************************************************
C
C   UTIL7      XM & DN                        FEB 2011    ArDean Leith
C              XM S2D                         APR 2013    ArDean Leith
C              'DN AD' REMOVAL                FEB 2020    ArDean Leith
C
C **********************************************************************
C=*                                                                    *
C=* Author: ArDean Leith                                               *                                                            *
C=* This file is part of:   SPIDER - Modular Image Processing System.  *
C=* SPIDER System Authors:  Joachim Frank & ArDean Leith               *
C=* Copyright 1985-2020  Health Research Inc.,                         *
C=* Riverview Center, 150 Broadway, Suite 560, Menands, NY 12204.      *
C=* Email: spider@health.ny.gov                                        *
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
C   UTIL7
C
C   PURPOSE: HANDLES OPERATIONS 'XM', 'DN'
C
C--*********************************************************************
             
        SUBROUTINE UTIL7()

        IMPLICIT NONE
		                                                                                        
        INCLUDE 'CMBLOCK.INC'
	INCLUDE 'CMLIMIT.INC'

        CHARACTER(LEN=1)      :: NULL = CHAR(0)
        CHARACTER(LEN=MAXNAM) :: FILNAM

        INTEGER               :: NDUM,MAXIM,MAXIM2,ITYPE
        INTEGER               :: NX1,NY1,NZ1,IRTFLG
        REAL                  :: FMIN1,FMAX1,SIG1,AV1

	INTEGER, PARAMETER    :: LUN1    = 11
	INTEGER, PARAMETER    :: LUN2    = 12
	INTEGER, PARAMETER    :: LUNDOC  = 80
	INTEGER, PARAMETER    :: LUNDOC2 = 82

        SELECT CASE(FCHAR(1:2))

        CASE ('XM') !  ------------------------------------   'XM'
           SELECT CASE(FCHAR(4:6))

           CASE ('MA') ! CREATE XMIPP SELFILE  -------------- 'XM MAKE'
              CALL XMSELFILE(LUNDOC,LUNDOC2)

           CASE ('S2D') ! STAR FILE TO DOC FILE  ------------ 'XM S2D'
              CALL STAR2DOC(LUNDOC,LUNDOC2)

           CASE DEFAULT
              CALL ERRT(101,'UNKNOWN OPERATION',NDUM)
           END SELECT


        CASE ('DN') !  -------------------------------------  'DN'

           IF (FCHAR(4:5) == 'AD') THEN ! ANISO DIFFUSION --- 'DN AD'
	      CALL UTIL_11()
              RETURN
           ENDIF


C          OPEN INPUT FILE
	   CALL OPFILEC(0,.TRUE.,FILNAM,LUN1,'O',ITYPE,
     &                    NX1,NY1,NZ1,
     &                    MAXIM,'INPUT',.FALSE.,IRTFLG)
	   IF (IRTFLG .NE. 0) GOTO 9999

           IF (IMAMI .NE. 1) CALL NORM3(LUN1,NX1,NY1,NZ1,
     &                                  FMAX,FMIN,AV)
           FMIN1 = FMIN
           FMAX1 = FMAX
           SIG1  = SIG
           AV1   = AV

C	   OPEN OUTPUT FILE
           MAXIM2 = 0
           IF (MAXIM > 0) MAXIM2 = MAXIM
	   CALL OPFILEC(LUN1,.TRUE.,FILNAM,LUN2,'U',ITYPE,
     &             NX1,NY1,NZ1,MAXIM2,'OUTPUT',.TRUE.,IRTFLG)
	   IF (IRTFLG .NE. 0) GOTO 9999

           SELECT CASE(FCHAR(4:5))

           CASE ('MS') ! MEAN SHIFT DENOISING  ---------------- 'DN MS'
              CALL MEANSHIFT(LUN1,LUN2,NX1,NY1,NZ1,
     &                       SIG1,IRTFLG)

           CASE ('ME')  ! MEDIAN FILTER ---------------------- 'DN MED'
              CALL MEDIAN(LUN1,LUN2,NX1,NY1,NZ1)

           CASE DEFAULT
              CALL ERRT(101,'UNKNOWN OPERATION',NDUM)
           END SELECT

        CASE DEFAULT
           CALL ERRT(101,'UNKNOWN OPERATION',NDUM)
        END SELECT

9999    CLOSE(LUN1)
        CLOSE(LUN2)
        CLOSE(LUNDOC)
        CLOSE(LUNDOC2)

	END

