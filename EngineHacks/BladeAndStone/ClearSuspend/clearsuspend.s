@ ASMC: InvalidateSuspendSave(SAVE_ID_SUSPEND). Used before returning to title at a demo ending.
.thumb
    mov  r0, #3
    ldr  r1, .Lfn
    bx   r1
    .align 2
.Lfn: .word 0x080A5A21
