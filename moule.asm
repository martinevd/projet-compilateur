extern printf, atoi, malloc, memcpy

section .data

DECL_VARS
argv: dq 0
fmt_int:db "%d", 10, 0
fmt_char: db "%c", 0
fmt_str: db "%s", 10, 0


global main
section .text

main:
push rbp
mov [argv], rsi

INIT_VARS
COMMANDE
RETOUR
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf

pop rbp
ret

_strlen:
    push rbp
    mov rbp, rsp
    mov rcx, 0
    mov rax, rdi
    jmp _loop

_loop:
    cmp byte [rax], 0
    je _end
    inc rax
    inc rcx
    jmp _loop

_end:
    mov rax, rcx
    jmp _ret

_ret:
    leave 
    ret 
