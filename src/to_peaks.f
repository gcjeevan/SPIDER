C **********************************************************************
C
C TO_PEAKS      NEW                                  FEB 14 ARDEAN LEITH
C               FINDMINMAX NSEPER PARAMETER          MAR 16 ARDEAN LEITH
C **********************************************************************
C=*                                                                    *
C=* This file is part of:   SPIDER - Modular Image Processing System.  *
C=* SPIDER System Authors:  Joachim Frank & ArDean Leith               *
C=* Copyright 1985-2016  Health Research Inc.,                         *
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
C TO_PEAKS
C
C PURPOSE:  CREATE POLAR REPRESENTATION OF IMAGE WITH RAYS ALONG THE
C           X DIMENSION.
C
C **********************************************************************

        SUBROUTINE TO_PEAKS

        IMPLICIT NONE
        INCLUDE 'CMBLOCK.INC'
        INCLUDE 'CMLIMIT.INC' 
 
        CHARACTER(LEN=MAXNAM) :: FILNAM,PROFILE,DOCNAM
        CHARACTER(LEN=72)     :: FORMOUT
        CHARACTER(LEN=96)     :: COMMENT

        REAL, ALLOCATABLE     :: BUF(:,:)
        REAL, ALLOCATABLE     :: OUT(:,:)
        REAL, ALLOCATABLE     :: RAYCURVE(:),RADCURVE(:)
        REAL, ALLOCATABLE     :: RAYSUM(:)

        REAL                  :: DLIST(8)
        INTEGER               :: LOCVAL(1)
        CHARACTER(LEN=3)      :: MODE
        LOGICAL               :: HALFCIRC
        INTEGER               :: MAXIM,ITYPE,NX,NY,NZ,IRTFLG,IER,NLET
        INTEGER               :: NA,NRAYS,NR,IXC,IYC
        INTEGER               :: NRAD,NXP,NYP,IRAY,IRAD
        REAL                  :: PI,DFI,FI,XS,YS,VTMP,VMIN,FMAXDIF
        REAL                  :: VMAX
        LOGICAL               :: WANTLINES

        INTEGER               :: NLET1
        INTEGER               :: IRAY_MIN,IRAY_MAX,IANG_MINAVG
        real                  :: UNUSED
        LOGICAL               :: SAVDOC

        LOGICAL               :: ADDEXT,GETNAME,ISOLD
        LOGICAL               :: APPEND,MESSAGE,NEWFILE
        INTEGER               :: LUNDOCNO,NLETD,KEY,NDIGITS
 
        INTEGER, PARAMETER    :: NUMMINS = 2 
        INTEGER, PARAMETER    :: NUMMAXS = 2
        INTEGER               :: LOCVALLEY(NUMMINS),LOCRIDGE(NUMMAXS)
        REAL                  :: VALVALLEY(NUMMINS),VALRIDGE(NUMMAXS)
        INTEGER               :: NMIN,NMAX
        REAL                  :: AVG_LOC_MIN1_ON_RAY, COG
        REAL                  :: AVG_LOC_MIN2_ON_RAY
        INTEGER               :: LOC_MIN1_ON_RAY,IAVG_LOC_MIN1_ON_RAY 
        INTEGER               :: LOC_MIN2_ON_RAY,IAVG_LOC_MIN2_ON_RAY 
        INTEGER               :: IAVG_LOC_MIN_ON_RAY 
        INTEGER               :: LOC_MIN_ON_RAD, N,  ICOG, IANG_COG 
        INTEGER               :: IANG_MIN,LOC_MAX_ON_RAD
        REAL                  :: FMINT,FMAXT,FHI,FLOW
        REAL                  :: RANGENEW,RANGEOLD,CON,CON2

        REAL                  :: quadri

        INTEGER, PARAMETER    :: LUNIN   = 20
        INTEGER, PARAMETER    :: LUNOUT  = 21
        INTEGER, PARAMETER    :: LUNPRO  = 22
        INTEGER, PARAMETER    :: LUNDOCN = 80

        CHARACTER(LEN=1)      :: NULL   = CHAR(0)


C       GET NAME FOR INPUT FILE
        MAXIM = 0
        CALL OPFILEC(0,.TRUE.,FILNAM,LUNIN,'O',ITYPE,NX,NY,
     &              NZ,MAXIM,'INPUT',.FALSE.,IRTFLG)
        IF (IRTFLG .NE. 0) RETURN

        IF (NZ > 1)  THEN
           CALL ERRT(101,'DOES NOT WORK ON VOLUMES',IER)
           RETURN
        ENDIF

C       GET NAME FOR POLAR OUTPUT FILE
        CALL FILERD(FILNAM,NLET,NULL,'POLAR OUTPUT',IRTFLG)
        IF (IRTFLG .NE. 0) GOTO 9999

C       GET NAME FOR PROFILE OUTPUT FILE
        CALL FILERD(PROFILE,NLET1,NULL,'PROFILE OUTPUT',IRTFLG)
        IF (IRTFLG .NE. 0) GOTO 9999

        CALL RDPRMC(MODE,NA,.TRUE.,
     &              'FULL OR HALF CIRCLE (F/H)',NULL,IRTFLG)
        IF (IRTFLG .NE. 0) GOTO 9999

        HALFCIRC  = (INDEX(MODE,'H') > 0)
        WANTLINES = (INDEX(MODE,'L') > 0)
	PI        = 4*DATAN(1.0D0)

C       FIND DEFAULT LENGTH OF RAYS = RADIUS = Y
        NRAD = MIN(((NX-1)/2), ((NY-1)/2))  ! LENGTH OF RAY = X SIZE

C       FIND DEFAULT NUMBER OF RAYS = CIRCUMFERANCE = X
        NRAYS = INT(2*PI*NRAD)                ! LEN. OF CIR = # OF RAYS
	IF (HALFCIRC) NRAYS = INT(PI*NRAD)    ! USED FOR POWER SPECTRA

        WRITE(NOUT,99)'  DEFAULT RADIUS: ',NRAD,
     &                '   DEFAULT RAYS:', NRAYS
 99     FORMAT(A,I0,A,I0)

        CALL RDPRI2S(NRAD,NRAYS,UNUSED,'RADIUS & NUMBER OF RAYS',IRTFLG)
        IF (IRTFLG .NE. 0) GOTO 9999

        NXP  = NRAD + 1                       ! X SIZE
        NYP  = NRAYS                          ! Y SIZE

        DFI  = 2 * PI / NYP                   ! RADIANS 
	IF (HALFCIRC) DFI = PI / NYP

        !write(6,*) '  pi:',pi,'rad:',nrad,' dfi:',dfi

C       OPEN OUTPUT FILE USING ABOVE NAME
        MAXIM = 0
	ITYPE = 1
        CALL OPFILEC(0,.FALSE.,FILNAM,LUNOUT,'N',ITYPE,NXP,NYP,
     &               1,MAXIM,' ',.FALSE.,IRTFLG)
        IF (IRTFLG .NE. 0) RETURN

C       OPEN PROFILE OUTPUT FILE USING ABOVE NAME
        MAXIM = 0
	ITYPE = 1
        CALL OPFILEC(0,.FALSE.,PROFILE,LUNPRO,'N',ITYPE,NYP,1,
     &               1,MAXIM,' ',.FALSE.,IRTFLG)
        IF (IRTFLG .NE. 0) RETURN

        ALLOCATE (BUF(NX,NY),
     &            OUT(NXP,NYP),      ! NRAD + 1 x NRAYS
     &            RAYSUM(NRAYS), 
     &            RAYCURVE(NXP), 
     &            RADCURVE(NYP), 
     &            STAT=IRTFLG)
        IF (IRTFLG .NE. 0) THEN 
           CALL ERRT(46,'TO_RAYS; BUF, OUT',NX*NY + NXP*NYP + 2*NRAYS)
           GOTO 9999
        ENDIF

C       LOAD INPUT IMAGE
        CALL REDVOL(LUNIN,NX,NY, 1,1, BUF,IRTFLG)
           
        RAYSUM = 0.0
	IXC    = NX/2+1     ! X CENTER
	IYC    = NY/2+1

        !write(6,*) ' Center:(',ixc,iyc,')  rad,rays:',nrad,nrays
        !write(6,*) ' nxp, nyp:',nxp, nyp

C       CREATE POLAR REPRESENTATION
C       NOTE: ALGORITHM IS DEPENDENT ON CIRCULAR CLOSURE IN QUADRI!

	DO  IRAD=0, NRAD       ! OVER ALL RADII
          DO IRAY=1,NRAYS      ! NRAYS     ! OVER ALL POINTS ON CIRCLE 

	     FI   = (IRAY-1) * DFI
	     XS   = COS(FI)  * IRAD
	     YS   = SIN(FI)  * IRAD

             VTMP = QUADRI(XS+IXC,YS+IYC,NX,NY,BUF)
             !if (iray == 1) buf(XS+IXC,YS+IYC) = 255 
             !if (iray == 5) buf(XS+IXC,YS+IYC) = 255 

	     OUT(IRAD+1,IRAY) = VTMP

             !write(6,*) irad,iray,xs+ixc,ys+iyc,vtmp
             !if ((j+1) == 43)write(6,*) irad,iray,xs+ixc,ys+iyc,vtmp 

             RAYSUM(IRAY) = RAYSUM(IRAY) + VTMP   ! FOR ROTATIONAL AVG.
          ENDDO
	ENDDO

        !call CHKFILE('jnkchk',55,1,NX,NY,1, BUF,IRTFLG)

               
C       FIND VALUES FOR LINE OVERLAYS
        VMIN = MINVAL(OUT)          ! MINUMUM OF IMAGE
        VMAX = MAXVAL(OUT)          ! MAXIMUM OF IMAGE

C       FIND AVERAGE FOR EACH RING USING ARRAY OP
        RAYSUM = RAYSUM / NRAD + 1  ! AVERAGE FOR EACH RAY
  
C       FIND LOCATION OF HIGHEST RAY AVERAGE 
        LOCVAL    = MAXLOC(RAYSUM)  ! RETURNS ARRAY OF LENGTH: 1
        IRAY_MAX  = LOCVAL(1)

C       FIND LOCATION OF LOWEST RAY AVERAGE 
        LOCVAL      = MINLOC(RAYSUM) ! RETURNS ARRAY OF LENGTH: 1
        IRAY_MIN    = LOCVAL(1)
        IANG_MINAVG = (360.0 / FLOAT(NRAYS)) * (IRAY_MIN -1)

        AVG_LOC_MIN1_ON_RAY = 0.0
        AVG_LOC_MIN2_ON_RAY = 0.0

        DO IRAY=1,NRAYS      ! LOOP OVER ALL RAYS 
           RAYCURVE  = OUT(:,IRAY)
           LOCVAL    = MINLOC(RAYCURVE) ! RETURNS ARRAY OF LENGTH: 1
        
           !write(6,*) ' raycurve:',raycurve(1:20)

           CALL FINDMINMAX(RAYCURVE,NRAD,
     &             LOCVALLEY,LOCRIDGE, VALVALLEY,VALRIDGE,
     &             NUMMINS,NUMMAXS,1, NMIN,NMAX,IRTFLG)

           !write(6,90) ' locvalley:',locvalley(1),' ',locvalley(2)

           AVG_LOC_MIN1_ON_RAY = AVG_LOC_MIN1_ON_RAY + LOCVALLEY(1)
           AVG_LOC_MIN2_ON_RAY = AVG_LOC_MIN2_ON_RAY + LOCVALLEY(2) 
 
        ENDDO

        IAVG_LOC_MIN1_ON_RAY = NINT(AVG_LOC_MIN1_ON_RAY / NRAYS)
        IAVG_LOC_MIN2_ON_RAY = NINT(AVG_LOC_MIN2_ON_RAY / NRAYS)

        !write(6,90) 'IAVG_LOC_MIN1_ON_RAY: ', iavg_loc_min1_on_ray
        !write(6,90) 'IAVG_LOC_MIN2_ON_RAY: ', iavg_loc_min2_on_ray

        IAVG_LOC_MIN_ON_RAY = IAVG_LOC_MIN1_ON_RAY
        IF (IAVG_LOC_MIN_ON_RAY <11) THEN
           IAVG_LOC_MIN_ON_RAY = IAVG_LOC_MIN2_ON_RAY
        ENDIF

        RADCURVE       = OUT(IAVG_LOC_MIN_ON_RAY,:)
        !write(6,*) ' radcurve:',radcurve
        LOCVAL         = MINLOC(RADCURVE) 
        LOC_MIN_ON_RAD = LOCVAL(1) 
        IANG_MIN       = 360.0 * FLOAT(LOC_MIN_ON_RAD-1)/FLOAT(NYP)
        !write(6,*) ' radcurve:',radcurve
        !write(6,90) 'LOC_MIN_ON_RAD:',loc_min_on_rad
90      FORMAT(2X, 5(A,I3))

C       OUTPUT PROFILE IMAGE
        CALL WRTVOL(LUNPRO,NYP,1, 1,1, RADCURVE,IRTFLG)

C       INVERT CONTRAST ON RADCURVE
        RADCURVE       = 255 - RADCURVE

        LOCVAL         = MINLOC(RADCURVE) ! actually max
        LOC_MAX_ON_RAD = LOCVAL(1) 

        !write(6,*) ' radcurve:',radcurve
        !write(6,90) 'loc_max_on_rad:',loc_max_on_rad

C       FIND CENTER OF GRAVITY OF CIRCLE AT DESIRED RADIUS
        COG  = 0.0
        DO N = LOC_MAX_ON_RAD, NYP
           COG = COG + RADCURVE(N) * N
        ENDDO
        DO N = 1,LOC_MAX_ON_RAD - 1
           COG = COG + RADCURVE(N) * (N + NYP - LOC_MAX_ON_RAD)
        ENDDO

        ICOG     = NINT(COG / SUM(RADCURVE)) + LOC_MAX_ON_RAD -1
        IF (ICOG > NYP ) ICOG = ICOG - NYP

        if (icog <1 .or. icog > nyp) then
            write(6,90) 'LOC_MAX_ON_RAD:',loc_max_on_rad,cog
            call errt(102,' bad icog',icog)
            stop
        endif

        IANG_COG = 360.0 * FLOAT(ICOG - 1) / FLOAT(NYP)
        IANG_COG = MOD(IANG_COG,360)

        write(6,90) 'RADIUS1:',      IAVG_LOC_MIN1_ON_RAY,
     &              '  RADIUS2:',    IAVG_LOC_MIN2_ON_RAY,
     &              '  MIN_AT_RAY:', LOC_MIN_ON_RAD,
     &              '  MIN COG:',    ICOG,
     &              '  MIN ANGLE:',  IANG_MIN,
     &              '  COG ANGLE:',  IANG_COG

C       SAVE PARAMETERS
        DLIST(1) = IRAY_MIN
        DLIST(2) = IRAY_MAX
        DLIST(3) = IANG_MINAVG          
        DLIST(4) = IANG_COG      
        DLIST(5) = IANG_MIN      
        DLIST(6) = IAVG_LOC_MIN_ON_RAY

        CALL REG_SET_NSELA(6,DLIST,.TRUE.,IRTFLG)
C       OUTPUT IMAGE
        CALL WRTVOL(LUNOUT,NXP,NYP, 1,1, OUT,IRTFLG)

C       OUTPUT PROFILE IMAGE
      !!  CALL WRTVOL(LUNPRO,NYP,1, 1,1, RADCURVE,IRTFLG)

C       OUTPUT PARAMETER DOC FILE
        ADDEXT  = .TRUE.
        GETNAME = .TRUE.
        ISOLD   = .FALSE.
        APPEND  = .TRUE.
        MESSAGE = .FALSE. 
        IRTFLG  = -8         ! NO IC USE

        CALL OPENDOC(DOCNAM,ADDEXT,NLETD,LUNDOCN,LUNDOCNO,GETNAME,
     &      'OUTPUT DOC',ISOLD,APPEND,MESSAGE,NEWFILE,IRTFLG)
        IF (IRTFLG > 0) GOTO 9999

        SAVDOC = (IRTFLG == 0)
        IF (SAVDOC) THEN

C                   123456789 123456789 123456789 123456789 123456789 123456789
c           COMMENT='  NUM,     S,          ANG_S,        V_S,       '//
c     &             '  L,           ANG_L,        V_L'
c           !CALL LUNDOCPUTCOM(LUNDOCNO,COMMENT(1:80),IRTFLG)

C          SET KEY NUMBER == IMAGE NUMBER
           CALL GETFILENUM(FILNAM,KEY,NDIGITS,.TRUE.,IRTFLG)

           FORMOUT  = 
     &      '(I7,1X,I2,1X,F5.0,3X,F6.3,2X,F5.0,1X,F6.3,3X,F6.2,1X,'//
     &      'F8.3,2X,F5.0)'
C            123456789 123456789 123456789 123456789 123456789 123456789 1234
           CALL LUNDOCWRTDATF(LUNDOCNO,KEY,DLIST,6,FORMOUT,IRTFLG)
        ENDIF

9999    IF (ALLOCATED(BUF))     DEALLOCATE (BUF)
        IF (ALLOCATED(OUT))     DEALLOCATE (OUT)
        IF (ALLOCATED(RAYSUM))  DEALLOCATE (RAYSUM)
        IF (ALLOCATED(RAYCURVE))DEALLOCATE (RAYCURVE)
        IF (ALLOCATED(RADCURVE))DEALLOCATE (RADCURVE)

        CLOSE(LUNIN)
        CLOSE(LUNOUT) 
        CLOSE(LUNDOCN) 
        CLOSE(LUNPRO) 
 
        END
#ifdef NEVER

           LOC_MIN_ON_RAY  = LOCVAL(1)
C       FIND CENTER OF GRAVITY OF CIRCLE AT DESIRED RADIUS
        COG  = 0.0
        DO N = LOC_MIN_ON_RAD, NYP
           COG = COG + RADCURVE(N) * N
        ENDDO
        DO N = 1,LOC_MIN_ON_RAD - 1
           COG = COG + RADCURVE(N) * (NYP - LOC_MIN_ON_RAD + N)
        ENDDO
        ICOG     = NINT(COG / SUM(RADCURVE))  + LOC_MIN_ON_RAD -1
        IANG_COG = 360.0 * FLOAT(ICOG - 1) / FLOAT(NYP)
        IANG_COG = MOD(IANG_COG,360)
#endif

