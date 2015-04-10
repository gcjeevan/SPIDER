C++*********************************************************************
C
C $$ SHIFT3.FOR
C
C **********************************************************************
C=*                                                                    *
C=* This file is part of:   SPIDER - Modular Image Processing System.  *
C=* SPIDER System Authors:  Joachim Frank & ArDean Leith               *
C=* Copyright 1985-2010  Health Research Inc.,                         *
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
C
C $$ SHIFT3:
C 
C THREE-DIMENSIONAL CIRCULAR SHIFT
C
	SUBROUTINE SHIFT3(LUN1,LUN2,NSAM,NROW,NSLICE,NSAMS,NROWS,NSLICS)

	NZ = MOD(NSLICS,NSLICE)
	IF(NZ.LT.0) NZ = NZ + NSLICE
	IF(NZ.EQ.0) GOTO 300
	LEND = NSLICE-NZ
	DO  L = 1,LEND
	JROFF = (L-1)*NROW
	JWOFF = (L+NZ-1)*NROW
	CALL SHIFTT(LUN1,LUN2,NSAM,NROW,NSAMS,NROWS,JROFF,JWOFF)
	ENDDO
	DO  L = LEND+1,NSLICE
	JROFF = (L-1)*NROW
	JWOFF = (L-LEND-1)*NROW
	CALL SHIFTT(LUN1,LUN2,NSAM,NROW,NSAMS,NROWS,JROFF,JWOFF)
	ENDDO
	RETURN
300	DO  L = 1,NSLICE
	JROFF = (L-1)*NROW
	CALL SHIFTT(LUN1,LUN2,NSAM,NROW,NSAMS,NROWS,JROFF,JROFF)
	ENDDO
	END