extern printf, atoi, malloc, strcpy, strcat, sprintf

section .data


argv: dq 0
fmt_int: db "%d", 10, 0
fmt_str: db "%s", 10, 0
fmt_char: db "%c", 10, 0
str_0: db "hello ", 0
str_1: db "world", 0


global main
section .text

main:
push rbp
mov rbp, rsp
mov [argv], rsi



call exec

mov rsp, rbp
pop rbp
ret

exec:
push rbp
    mov rbp, rsp
    sub rsp, 8
lea rax, [rel str_0]
mov [rbp - 8], rax

sub rsp, 8
lea rax, [rel str_1]
mov [rbp - 16], rax


mov rax, [rbp - 8]
push rax              
mov rax, [rbp - 16]
pop rdi               
mov rsi, rax          
call concat_strings  

mov rsi, rax
mov rdi, fmt_str
xor rax, rax
call printf

mov rax, [rbp - 8]
mov rdi, rax
call strlen
mov rsi, rax
mov rdi, fmt_int
xor rax, rax
call printf

sub rsp, 8
mov rax, [rbp - 8]
mov rdi, rax
call strlen
push rax
mov rax, 1
mov rbx, rax
pop rax
sub rax, rbx
mov [rbp - 24], rax

loop0:mov rax, [rbp - 24]
cmp rax, 0
jz end0

mov rax, [rbp - 8]         
push rax
mov rax, [rbp - 8]
mov rdi, rax
call strlen
push rax
mov rax, [rbp - 24]
mov rbx, rax
pop rax
sub rax, rbx
push rax
mov rax, 1
mov rbx, rax
pop rax
sub rax, rbx       
mov rbx, rax        
pop rax           
add rax, rbx        
movzx rax, byte [rax]  

mov rsi, rax
mov rdi, fmt_char
xor rax, rax
call printf

mov rax, [rbp - 24]
push rax
mov rax, 1
mov rbx, rax
pop rax
sub rax, rbx
mov [rbp - 24], rax
jmp loop0
end0: nop

end_exec:
    mov rsp, rbp
    pop rbp
    ret
    


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

