;
; PURPOSE: Test BP RP - 3D iterative back projection with constraints, ||
; SOURCE:  testbprp.tst     (INDEXED)

 MD   ; Turn off some un-necessary file IO and docfile output
   VB OFF

 ; Create 75 x 75 x75 volume with sphere inside
 MO 3
   jnkvolbprp        ; File     (output)
   75,75, 75
   SP                ; Sphere
   N
   1
   9,3
   30,29,28
   0,0,0

 ; Create inline stack for 20 images
 MS
   _8@          ; Inline file   (output)
   75,75,1      ; Size
   20           ; 20 images

 ; Compute projections of a 3D volume using three Eulerian angles. 
 PJ 3Q
   jnkvolbprp    ; Volume                (input)
   35            ; Projection radius
   1-20          ; Desired angles
   savangbprp    ; Angles file           (input)
   _8@****       ; Stack for projections (output)

 MY FL           ; Flush results file 

 ; Run iterative backprojection now
 BP RP [iter]
   _8@****        ; Imput images (projections)
   1-20           ; Selection file for projection files
   23             ; Radius
   savangbprp     ; Angles doc file      (input)
   *              ; No symmetries
   jnkvolbprpout  ; Volume               (output)
   1.0e-4, 0.0    ; Lambda, correction limit
   3,0            ; Iterations, constraints mode
   1.77, 1.90     ; Minimum, maximum
   0.9994         ; Smoothing const (0-0.999)

 FS [max],[min]   ; Get volume statistics
   jnkvolbprpout  ; Input file

 SYS               ; Echo number of iterations
   echo ' No. iterations: {****[iter]}'
 SYS               ; Echo volume statistics
   echo ' BP RP    Range: {%g13.5%[min]}...{%g13.5%[max]}'
 SYS
   echo ' Correct  Range:  -0.48811E-03...  0.93562E-01' ; echo
 
 EN
