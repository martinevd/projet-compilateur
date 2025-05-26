extern printf, atoi

section .data


argv: dq 0
fmt_int:db "%d", 10, 0

global main
section .text

main:
push rbp
mov [argv], rsi
mov rbp, rsp



sub rsp, 4
mov rax, 10
mov [rbp-4], eax

 
sub rsp, 4
mov rax, 0
mov [rbp-8], eax

 
sub rsp, 8
mov rax, 1
mov [rbp-16], rax

 
sub rsp, 8
mov rax, 1
mov [rbp-24], rax

 
loop0: mov eax, [rbp-4]
cmp rax, 0
jz end0

mov eax, [rbp-4]
push rax
mov rax, 1
mov rbx, rax
pop rax
sub rax, rbx
mov [rbp-4], eax

 
mov eax, [rbp-8]
push rax
mov rax, 1
mov rbx, rax
pop rax
add rax, rbx
mov [rbp-8], eax

 
mov rax, [rbp-24]
push rax
mov rax, [rbp-16]
mov rbx, rax
pop rax
add rax, rbx
mov [rbp-24], rax

jmp loop0
end0: nop

mov rax, [rbp-24]
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf

add rsp, 24
pop rbp
ret


