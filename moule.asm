extern printf, atoi

section .data
DECL_VARS
argv: dq 0
fmt_int: db "%d", 10, 0

global main
section .text

main:

    push rbp
    mov rbp, rsp

    mov [argv], rsi

    INIT_VARS

    CALL_MAIN

    mov rsi, rax
    mov rdi, fmt_int
    xor rax, rax
    call printf

    mov rsp, rbp
    pop rbp
    ret

COMMANDE



;RETOUR
;mov rdi, fmt_int
;mov rsi, rax
;xor rax, rax
;call printf

;VIDE_MEMOIRE
;pop rbp
;ret

