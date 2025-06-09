extern printf, atoi

section .data


argv: dq 0
fmt_int: db "%d", 10, 0
fmt_str: db "%s", 10, 0


global main
section .text

main:
push rbp
mov rbp, rsp
mov [argv], rsi



call exec

mov rsi, rax
mov rdi, fmt_int
xor rax, rax
call printf

mov rsp, rbp
pop rbp
ret

exec:
push rbp
    mov rbp, rsp
    sub rsp, 8
lea rax, [str_0]
mov [rbp - 8], rax

mov rax, [rbp - 8]
mov rsi, rax
mov rdi, fmt_str
xor rax, rax
call printf

mov rax, [rbp - 8]
    jmp end_exec
    
end_exec:
    mov rsp, rbp
    pop rbp
    ret
    



