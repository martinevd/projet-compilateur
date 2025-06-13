extern printf, atoi

section .data

x: dq 0
LC0: dq 0x4002666666666666

argv: dq 0
fmt_int:db "%d", 10, 0
fmt_double: db "%lf", 10, 0

global main
section .text

main:
push rbp
mov [argv], rsi

mov rbx, [argv]
mov rdi, [rbx + 8]
call atoi
mov [x], rax

movsd xmm0, [LC0]
movsd [x], xmm0
 mov rax, [x]
mov rsi, fmt_int
mov rdi, rax
xor rax, rax
call printf

mov rax, 0

pop rbp
ret
