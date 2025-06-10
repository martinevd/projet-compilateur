extern printf, atoi, malloc, strcpy, strcat, sprintf

section .data
DECL_VARS

argv: dq 0
fmt_int: db "%d", 10, 0
fmt_str: db "%s", 10, 0
fmt_char: db "%c", 10, 0
DECL_STRINGS

global main
section .text

main:
push rbp
mov rbp, rsp
mov [argv], rsi

INIT_VARS

CALL_EXEC

mov rsp, rbp
pop rbp
ret

COMMANDE

strlen:
    push rbp
    mov rbp, rsp
    mov rcx, 0
    mov rax, rdi
    jmp loop_strlen
loop_strlen:
    cmp byte [rax], 0
    je end_strlen
    inc rax
    inc rcx
    jmp loop_strlen
end_strlen:
    mov rax, rcx
    jmp ret_strlen
ret_strlen:
    leave 
    ret 

concat_strings:
    push rbp
    mov rbp, rsp
    sub rsp, 16      

    mov [rbp-8], rdi  
    mov [rbp-16], rsi

    mov rdi, [rbp-8]
    call strlen
    mov rcx, rax

    mov rdi, [rbp-16]
    call strlen
    add rcx, rax
    add rcx, 1

    mov rdi, rcx
    call malloc

    mov rdi, rax   
    mov rsi, [rbp-8]
    call strcpy

    mov rsi, [rbp-16]
    call strcat

    mov rsp, rbp
    pop rbp
    ret
