@ Blade & Stone: data-driven GetPlayerLeaderPid (replaces FE8U 0x08033258).
@ Returns BS_LeaderTable[chapterIndex] if nonzero; otherwise vanilla behaviour
@ (Ephraim on the Ephraim route, Eirika otherwise).
.thumb
.global BS_GetPlayerLeaderPid
BS_GetPlayerLeaderPid:
    ldr   r2, .Lplayst
    ldrb  r0, [r2, #0x0E]      @ gPlaySt.chapterIndex
    ldr   r1, .Ltable
    ldrb  r0, [r1, r0]
    cmp   r0, #0
    bne   .Lret
    ldrb  r1, [r2, #0x1B]      @ gPlaySt.chapterModeIndex
    mov   r0, #0x01            @ Eirika
    cmp   r1, #3               @ Ephraim route
    bne   .Lret
    mov   r0, #0x0F            @ Ephraim
.Lret:
    bx    lr
    .align 2
.Lplayst: .word 0x0202BCF0
.Ltable:  @ word appended by EA (POIN BS_LeaderTable)
