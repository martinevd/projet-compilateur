extern printf, atoi, malloc, memcpy

section .data

x: dq 0
y: dq 0
str_0: db 104, 101, 108, 108, 111, 0
str_1: db 119, 111, 114, 108, 100, 0

argv: dq 0
fmt_int:db "%d", 10, 0
fmt_char: db "%c", 0
fmt_str: db "%s", 10, 0


global main
section .text

main:
push rbp
mov [argv], rsi

mov rbx, [argv]
mov rdi, [rbx + 8]
call atoi
mov [x], rax
mov rbx, [argv]
mov rdi, [rbx + 16]
call atoi
mov [y], rax

lea rax, [rel str_0]
mov [x], rax
lea rax, [rel str_1]
mov [y], rax

; === CONCATENATION START ===
mov rax, [x]
mov rdi, rax
call _strlen
mov rbx, rax
mov r12, rdi

mov rax, [y]
mov rdi, rax
call _strlen
mov rcx, rax
mov r13, rdi

mov rdx, rbx
add rdx, rcx
add rdx, 1           ; +1 pour le caractère nul (\0)
mov rdi, rdx
call malloc
mov r14, rax

mov rdi, r14
mov rsi, r12
mov rdx, rbx
call memcpy

add rdi, rbx
mov rsi, r13
mov rdx, rcx
call memcpy

add rdi, rcx
mov byte [rdi], 0

mov rax, r14
; === CONCATENATION END ===

mov rdi, fmt_str
mov rsi, rax
xor rax, rax
call printf

mov rax, 0
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

