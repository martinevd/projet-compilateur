extern printf, atoi

section .data
X: dq 0
Y: dq 0

argv: dq 0
fmt_int: db "%d", 10, 0

global main
section .text

main:
    push rbp
    mov rbp, rsp

    mov [argv], rsi

    mov rbx, [argv]
mov rdi, [rbx + 8]
call atoi
mov [X], rax
mov rbx, [argv]
mov rdi, [rbx + 16]
call atoi
mov [Y], rax


    call main_function

    mov rsi, rax
    mov rdi, fmt_int
    xor rax, rax
    call printf

    mov rsp, rbp
    pop rbp
    ret

add:
push rbp
    mov rbp, rsp
    sub rsp, 16
mov [rbp - 8], rdi
mov [rbp - 16], rsi
if0:mov rax, [rbp - 16]
cmp rax, 0
jz else0
mov rax, [rbp - 8] 
push rax
mov rax, 1
mov rbx, rax
pop rax
add rax, rbx
mov [rbp - 8], rax
mov rax, [rbp - 16] 
push rax
mov rax, 1
mov rbx, rax
pop rax
sub rax, rbx
mov [rbp - 16], rax
mov rax, [rbp - 16]
push rax
mov rax, [rbp - 8]
push rax
pop rdi
pop rsi
call add

    jmp end_add
    
jmp end0
else0: nop
end0: nop

mov rax, [rbp - 8]
    jmp end_add
    
end_add:
    mov rsp, rbp
    pop rbp
    ret
    
main_function:
push rbp
    mov rbp, rsp
    mov rax, [Y]
push rax
mov rax, [X]
push rax
pop rdi
pop rsi
call add

    jmp end_main_function
    
end_main_function:
    mov rsp, rbp
    pop rbp
    ret
    



