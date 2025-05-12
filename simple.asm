extern printf, atoi

section .data

X: dq 0
Y: dq 0

argv: dq 0
fmt_int:db "%d", 10, 0

global main
section .text

main:
push rbp
mov [argv], rsi

mov rbx, [argv]
mov rdi, [rbx + 8]
call atoi
mov [X], rax
mov rbx, [argv]
mov rdi, [rbx + 16]
call atoi
mov [Y], rax

loop0:mov rax, [X]
cmp rax, 0
jz end0
mov rax, [X] 
push rax
mov rax, 1
mov rbx, rax
pop rax
sub rax, rbx
mov [X], rax
 mov rax, [Y] 
push rax
mov rax, 1
mov rbx, rax
pop rax
add rax, rbx
mov [Y], rax
jmp loop0
end0: nop

mov rax, [Y]
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf

pop rbp
ret


