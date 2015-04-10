
C++*********************************************************************
C
C SETMODE                  REMOVED FROM DRIVER.F   MAR 93 ARDEAN LEITH
C                          F90 CHANGES           APRIL 98 ARDEAN LEITH
C                          NO RESULTS ADDED       SEPT 98 ARDEAN LEITH
C                          ADDED SET REGS          AUG 00 ARDEAN LEITH
C                          SET MEM REMOVED         JAN 01 ARDEAN LEITH
C                          REG PIPE ADDED          JUL 01 ARDEAN LEITH
C                          DELAY FREE              JUN 02 ARDEAN LEITH
C                          OMP_GET_NUM_PROCS       JUL 03 ARDEAN LEITH
C                          RDPRI1S(ISEED           OCT 03 ARDEAN LEITH
C                          NOUT REDIRECT           OCT 03 ARDEAN LEITH
C                          SELECT REWRITE          NOV 03 ARDEAN LEITH
C                          TO_TERM                 DEC 03 ARDEAN LEITH
C                          SAVED ISEED             FEB 04 ARDEAN LEITH
C                          SET REGS REMOVED        NOV 05 ARDEAN LEITH
C                          LEGACY () INPUT         JUN 06 ARDEAN LEITH
C                          CVARS                   OCT 06 ARDEAN LEITH
C                          IF TERMOFF, NOUT   = 3  SEP 07 ARDEAN LEITH
C                          SET FFTW THREADS        DEC 07 ARDEAN LEITH
C                          SET USE_FBP_INTERP      JUN 11 ARDEAN LEITH
C                          SET USE_FBS_INTERP      JUL 11 ARDEAN LEITH
C                          NO USE_FBP_INTERP       SEP 11 ARDEAN LEITH
C                          USE_FBP_INTERP          APR 12 ARDEAN LEITH
C                          VERBOSE                 APR 12 ARDEAN LEITH
C                          UNUSED DELAY REMOVED    APR 13 ARDEAN LEITH
C                          OUTPUT FORMATTING       AUG 13 ARDEAN LEITH
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
C   SETMODE(RES_TO_TERM)
C
C   PURPOSE:   CONTAINS CODE FOR SETTING VARIOUS OPTIONAL MODES 
C
C23456789 123456789 123456789 123456789 123456789 123456789 123456789 12
C--*********************************************************************

        SUBROUTINE SETMODE(RES_TO_TERM)

        INCLUDE 'CMBLOCK.INC'
        INCLUDE 'CMLIMIT.INC'
 
C       RANDOM NUMBER GENERATOR SEED
        INTEGER, ALLOCATABLE  :: ISEEDVAL(:)
        INTEGER               :: OMP_GET_NUM_PROCS 


C       NUMBER OF OPERATIONS IN MODE MENU
        PARAMETER (IMOFNC = 27)
        CHARACTER(LEN=12)     :: MOMENU(IMOFNC)
        CHARACTER(LEN=12)     :: MODE

        CHARACTER(LEN=MAXNAM) :: PIPENAME,FILOPENED
        CHARACTER(LEN=1)      :: NULL = CHAR(0)
        LOGICAL               :: RESULTS,REGPIPE,TORESULTS,ISOPEN
        LOGICAL               :: RES_TO_TERM

        SAVE    FILOPENED,ISEED

        DATA MOMENU/'ME          ','STA        ',
     &              'TR ON       ','TR OFF     ',
     &              'OP ON       ','OP OFF     ',
     &              'VB ON       ','VB OFF     ',
     &              'INLN BUFF   ','SET MP     ',
     &              'SET MEM     ','SET SEED   ',
     &              'NO RESULTS  ','SET REGS   ',
     &              'PIPE        ','SET VARS   ',
     &              'RESULTS ON  ','RESULTS OFF',
     &              'TERM ON     ','TERM OFF   ',
     &              '() ON       ','() OFF     ',
     &              'FBS ON      ','FBS OFF    ',
     &              'LONGCOL ON  ','LONGCOL OFF',
     &              'SET THREADS '/

        DATA MPINUSE/0/ 
        DATA RESULTS/.TRUE./
        DATA REGPIPE/.FALSE./
        DATA TORESULTS/.FALSE./
        DATA USE_LONGCOL/.FALSE./

C       MODE SWITCH OPERATION
C       READ IN THE MODE.  IF NOTHING TYPED IN, GET NEXT OPERATION
9400    CALL RDPRMC(MODE,NLET,.TRUE.,'MODE',NULL,IRTFLG)
        IF (MODE(1:1) .EQ. ' ') RETURN

        SELECT CASE(MODE)

      CASE("ME")
C       MENU ------------------------------------------------------ ME
        WRITE(NOUT,9610)
9610    FORMAT(/
     &  '  ME          ',T19, ' MODE MENU'/
     &  '  STA         ',T19, ' STATUS OF MODES '/
     &  '  TR ON       ',T19, ' TRACE ON '/
     &  '  TR OFF      ',T19, ' TRACE OFF '/
     &  '  OP ON       ',T19, ' SHOW OPERATION '/
     &  '  OP OFF      ',T19, ' SHOW OPERATION OFF '/
     &  '  VB ON       ',T19, ' VERBOSE ON '/
     &  '  VB OFF      ',T19, ' VERBOSE OFF '/
     &  '  SET SEED    ',T19, ' SET RANDOM NUMBER SEED '/
     &  '  SET REGS    ',T19, ' SET NUMBER OF REGISTER VARIABLES '/
     &  '  SET VARS    ',T19, ' SET NUMBER OF SYMBOLIC VARIABLES '/
     &  '  RESULTS OFF ',T19, ' NO RESULTS FILE '/
     &  '  RESULTS ON  ',T19, ' USE RESULTS FILE '/
     &  '  PIPE        ',T19, ' OPEN REGISTER OUTPUT PIPE'/
     &  '  TERM ON     ',T19, ' OUTPUT TO TERMINAL, NOT RESULTS '/
     &  '  TERM OFF    ',T19, ' OUTPUT TO RESULTS, NOT TERMINAL '/
     &  '  () ON       ',T19, ' () NEEDED FOR SIMPLE LIST IN LOOP '/
     &  '  () OFF      ',T19, ' () NOT NEEDED FOR SIMPLE LIST IN LOOP '/
     &  '  FBS ON      ',T19, ' FBS INTERPOLATION USED '/
     &  '  FBS OFF     ',T19, ' FBS INTERPOLATION NOT USED '/
     &  '  LONGCOL ON  ',T19, ' LONG ALIGNMENT DOC FILE COLS '/
     &  '  LONGCOL OFF ',T19, ' SHORT ALIGNMENT DOC FILE COLS ')

#ifdef SP_MP
        WRITE(NOUT,9611)
9611    FORMAT(
     &  '  SET THREADS ',T19, ' SET NUMBER OF FFTW3 THREADS'/
     &  '  SET MP      ',T19, ' SET MAX. NO. OF PROCESSORS USED ')
#endif

        WRITE(NOUT,*) ' '


      CASE("STA")
C       DETERMINE STATUS ------------------------------------------ STA
        IF (NTRACE.EQ.1)      WRITE(NOUT,9630) MOMENU(3)(:10)
        IF (NTRACE.EQ.0)      WRITE(NOUT,9630) MOMENU(4)(:10)
        IF (NTRACE.LT.0)      WRITE(NOUT,9630) MOMENU(6)(:10)
        IF (NTRACE.EQ.0)      WRITE(NOUT,9630) MOMENU(5)(:10)
        IF (VERBOSE)          WRITE(NOUT,9630) MOMENU(7)(:10)
        IF (.NOT. VERBOSE)    WRITE(NOUT,9630) MOMENU(8)(:10)
        IF (LEGACYPAR)        WRITE(NOUT,9630) MOMENU(22)(:10)
        IF (.NOT. LEGACYPAR)  WRITE(NOUT,9630) MOMENU(23)(:10)
        IF (RESULTS)          WRITE(NOUT,*)' HAS RESULTS FILE'
        IF (.NOT. RESULTS)    WRITE(NOUT,*)' NO RESULTS FILE'
                              WRITE(NOUT,*)' RANDOM NUMBER SEED: ',ISEED
        IF (REGPIPE)          WRITE(NOUT,*)' REGISTER PIPE OPEN'
        IF (RES_TO_TERM)      WRITE(NOUT,*)' RESULTS OUTPUT TO TERMINAL'
        IF (USE_FBS_INTERP)   WRITE(NOUT,*)' FBS INTERPOLATION USED'
        IF (.NOT. USE_FBS_INTERP)  
     &                        WRITE(NOUT,*)' FBS INTERPOLATION NOT USED'
        IF (USE_LONGCOL)      WRITE(NOUT,*)' LONG  ALIGN DOC FILE COLS'
        IF (.NOT. USE_LONGCOL)WRITE(NOUT,*)' SHORT ALIGN DOC FILE COLS'

        CALL REG_GET_NUMS(IREGS,NCHAR)
                       WRITE(NOUT,*)' NUMBER OF REGISTERS: ',     IREGS
                       WRITE(NOUT,*)' NUMBER OF REGISTER CHAR.: ',NCHAR

        CALL SYMPAR_GET_NUMS(ICVARS,NCHAR)
                       WRITE(NOUT,*)' NUMBER OF VARIABLES: ',    ICVARS
                       WRITE(NOUT,*)' NUMBER OF VARIABLE CHAR.: ',NCHAR

#ifdef SP_MP
        WRITE(NOUT,*) ' NUMBER OF PROCESSORS USED:',MPINUSE
        WRITE(NOUT,*) ' NUMBER OF FFTW THREADS: ',NUMFFTWTH
#endif

9630    FORMAT(2X,A)
        GOTO 9400


      CASE("TR ON")
C       TRACE ON --------------------------------------------- TRACE ON
        NTRACE = 1

      CASE("TR OFF")
C       TRACE OFF ------------------------------------------- TRACE OFF
        NTRACE =  0

      CASE("OP ON")
C       SET OP ON ----------------------------------------------- OP ON
        NTRACE = -1

      CASE("VB ON","VERBOSE","VERBOSE ON")
C       SET VERBOSE FILE DATA ------------------------------ VERBOSE ON
        VERBOSE = .TRUE.

      CASE("VB OFF","NON VERBOSE","NOT VERBOSE")
C       SET NON-VERBOSE FILE DATA ------------------------- VERBOSE OFF
        VERBOSE = .FALSE.

      CASE("SET REGS")
C       SET NUMBER OF REGISTER VARIABLES  -------------------- SET REGS
        CALL REG_REINIT(IRTFLG)
        RETURN

      CASE("SET VARS")
C       SET NUMBER OF REGISTER VARIABLES  -------------------- SET VARS
        CALL SYMPAR_REINIT(IRTFLG)
        RETURN

      CASE("PIPE")
C       SEND REGISTER SETTINGS DOWN PIPE ------------------------ PIPE
C       ~9 ALLOWS EXTENSION
        CALL FILERD(PIPENAME,NLET,CHAR(0),'PIPE~9',IRTFLG)  
        CALL REG_OPENPIPE(PIPENAME(1:NLET),IRTFLG)


      CASE("SET MP")
C       SET NUMBER OF PROCESSORS WANTED ------------------------ SET MP
        CALL RDPRI1S(MPINUSE,NOT_USED,
     &             'NUMBER OF PROCESSORS WANTED (OR 0 FOR ALL)',IRTFLG)
        IF (IRTFLG .NE. 0) RETURN

#ifdef SP_MP
        IF (MPINUSE .LE. 0) THEN
C          GET NUMBER OF PROCESSORS WITH SYSTEM CALL
           MPINUSE = OMP_GET_NUM_PROCS()
           WRITE(NOUT,*) ' OMP PROCESSORS IN USE: ',MPINUSE 
        ENDIF

C       SET NUMBER OF PROCESSORS WITH SYSTEM CALL
        CALL  SETTHREADS(MPINUSE)
#else
        WRITE(NOUT,*) '*** NOT COMPILED FOR MULTIPLE PROCESSORS' 
#endif


      CASE("SET THREADS")
C       SET NUMBER OF FFTW THREADS ------------------------ SET THREADS
        CALL RDPRI1S(NUMFFTWTH,NOT_USED,
     &           'NUMBER OF FFTW THREADS WANTED (OR 0 FOR ALL)',IRTFLG)
        IF (IRTFLG .NE. 0) RETURN

#ifdef SP_MP
        IF (NUMFFTWTH .LE. 0) THEN
C          GET NUMBER OF PROCESSORS WITH SYSTEM CALL
           NUMFFTWTH = OMP_GET_NUM_PROCS()
           WRITE(NOUT,*) ' FFTW3 THREADS REQUESTED: ',NUMFFTWTH 
        ENDIF
#else
        WRITE(NOUT,*) '*** NOT COMPILED FOR MULTIPLE PROCESSORS' 
        WRITE(NOUT,*) ' FFTW3 THREADS ALLOWED: ',NUMFFTWTH 
#endif




      CASE("SET MEM")
C       SET ALLOCABLE MEMORY ---------------------------------- SET MEM
        CALL RDPRIS(IDUM,IDUM,NOT_USED,
     &             'SET MEM NO LONGER USED IN SPIDER ',IRTFLG)
        IF (IRTFLG .NE. 0) RETURN

      CASE("SET SEED")
C       SET RANDOM NUMBER SEED ------------------------------- SET SEED
        CALL RDPRI1S(ISEED,NOT_USED, 'NEW SEED',IRTFLG)
        CALL RANDOM_SEED(SIZE=NUMBITS)
        ALLOCATE(ISEEDVAL(NUMBITS))

        DO  I=1,NUMBITS 
           ISEEDVAL(I)= I * ISEED
        ENDDO

        CALL RANDOM_SEED(PUT=ISEEDVAL)
        DEALLOCATE(ISEEDVAL)

      CASE("RESULTS OFF", "NO RESULTS")
C       DESTROY RESULTS FILE ------------------------------- NO RESULTS
C       DESTROY RESULTS FILE ------------------------------- RESULTS OFF
        RESULTS = .FALSE.
        INQUIRE(UNIT=NDAT,OPENED=ISOPEN,NAME=FILOPENED)
        WRITE(NDAT,*) ' RESULTS FILE TERMINATED AT USERS REQUEST' 
        WRITE(NDAT,*) '  ' 
        CLOSE(NDAT)
        OPEN(NDAT,FILE='/dev/null',IOSTAT=IER)
        IF (IER .NE. 0) 
     &        STOP '*** SPIDER UNABLE TO OPEN /dev/null FILE ***'
        WRITE(NOUT,*) ' RESULTS FILE TERMINATED AT USERS REQUEST' 
        WRITE(NOUT,*) ' '


      CASE("RESULTS ON", "WANT RESULTS","RESULTS")
C       RESTART RESULTS FILE ------------------------------- RESULTS ON
        CLOSE(NDAT)
        OPEN(NDAT,FILE=FILOPENED,STATUS='OLD',POSITION='APPEND',
     &          IOSTAT=IER)
        IF (IER .EQ. 0) THEN
           WRITE(NOUT,*) ' RESULTS FILE REOPENED: ',FILOPENED 
        ENDIF

      CASE("TERM ON")
C       TERM ON ---------------------------------------------- TERM ON
C       FORCE OUTPUT TO TERMINAL NOT RESULTS FILE
        RES_TO_TERM = .TRUE.
        NDAT   = 6
        NOUT   = NDAT
        WRITE(NOUT,*) ' DIVERT ALL OUTPUT TO TERMINAL'

      CASE("TERM OFF")
C       TERM OFF   ------------------------------------------ TERM OFF
C       NORMAL OUTPUT TO RESULTS FILE NOT TERMINAL
        RES_TO_TERM = .FALSE.
        NDAT   = 3
        NOUT   = 3
        WRITE(NOUT,*) ' OUTPUT TO RESULTS FILE (NOT TERMINAL)' 
        WRITE(NOUT,*) ' '

      CASE("() ON")
C       () ON ------------------------------------------------- () ON
        LEGACYPAR = .TRUE.
        WRITE(NOUT,*) ' () NEEDED AROUND SIMPLE LIST IN INPUT LOOP'
        WRITE(NOUT,*) ' '

      CASE("() OFF")
C       () OFF   ---------------------------------------------- () OFF
        LEGACYPAR = .FALSE.
        WRITE(NOUT,*) ' () NOT NEEDED AROUND SIMPLE LIST IN INPUT LOOP'
        WRITE(NOUT,*) ' '

      CASE("FBS ON","USE FBS","FBS")
C       FBS ON ------------------------------------------------ FBS ON
        USE_FBS_INTERP = .TRUE.
        WRITE(NOUT,*) ' USING FBS INTERPOLATION'
        WRITE(NOUT,*) ' '

      CASE("FBS OFF","NO FBS")
C       FBS OFF-- --------------------------------------------- FBS ON
        USE_FBS_INTERP = .FALSE.
        WRITE(NOUT,*) ' NOT USING FBS INTERPOLATION'
        WRITE(NOUT,*) ' '

      CASE("LONGCOL ON","LONGCOL","LONG DOC COL")
C       LONGCOL ON ----------------------------------------- LONGCOL ON
        USE_LONGCOL = .TRUE.
        WRITE(NOUT,*) ' LONG ALIGNMENT DOC FILE COLUMNS'
        WRITE(NOUT,*) ' '

      CASE("LONGCOL OFF","SHORT DOC COL")
C       LONGCOL OFF --------------------------------------- LONGCOL OFF
        USE_LONGCOL = .FALSE.
        WRITE(NOUT,*) ' SHORT ALIGNMENT DOC FILE COLUMNS'
        WRITE(NOUT,*) ' '


      CASE DEFAULT
        WRITE(NOUT,*) '*** UNKNOWN MODE'

      END SELECT

      END
