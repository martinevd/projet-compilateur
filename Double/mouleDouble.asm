extern printf, atoi

section .data

DECL_VARS
argv: dq 0
fmt_int:db "%d", 10, 0
fmt_double: db "%lf", 10, 0

global main
section .text

main:
push rbp
mov [argv], rsi

INIT_VARS
COMMANDE
RETOUR

pop rbp
ret