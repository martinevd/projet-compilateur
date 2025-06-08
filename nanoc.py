from lark import Lark, Token

cpt = 0
strings = {}
string_labels = {}

g = Lark(r"""
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9]*/
NUMBER: /[1-9][0-9]*/|"0" 
STAR:"*"
OPBIN: /[+\-]/
STRING: /"[^"]*"/
         
liste_var:                            -> vide
    | IDENTIFIER ("," IDENTIFIER)*    -> vars
expression: IDENTIFIER            -> var
    | expression OPBIN expression -> opbin
    | NUMBER                      -> number
    | "char" STAR IDENTIFIER      -> char_p
    | STRING                      -> string
    | "len" "(" expression ")"    -> strlen    
    | expression "[" expression "]"  -> charat 
commande: commande (";" commande)*   -> sequence
    | "while" "(" expression ")" "{" commande "}" -> while
    | IDENTIFIER "=" expression              -> affectation
    | "if" "(" expression ")" "{" commande "}" ("else" "{" commande "}")? -> ite
    | "printf" "(" expression ")"                -> print
    | "skip"                                  -> skip
program:"main" "(" liste_var ")" "{"commande"return" "("expression")" "}"
%import common.WS
%ignore WS
""", start='program')


def collect_strings_expression(e):
    global strings, string_labels
    if isinstance(e, Token):
        return
    if e.data == "string":
        val = e.children[0].value.strip('"')
        if val not in string_labels:
            label = f"str_{len(strings)}"
            string_labels[val] = label
            strings[label] = val + '\0'
    elif e.data in ("opbin", "strlen"):
        for child in e.children:
            collect_strings_expression(child)
    elif e.data == "char_p":
        pass
    elif e.data == "charat":
        collect_strings_expression(e.children[0])
        collect_strings_expression(e.children[1])
    elif e.data in ("var", "number"):
        pass
    else:
        for child in e.children:
            if hasattr(child, "data"):
                collect_strings_expression(child)


def collect_strings_commande(c):
    if c.data == "affectation":
        collect_strings_expression(c.children[1])
    elif c.data == "print":
        collect_strings_expression(c.children[0])
    elif c.data == "while":
        collect_strings_expression(c.children[0])
        collect_strings_commande(c.children[1])
    elif c.data == "sequence":
        for child in c.children:
            collect_strings_commande(child)
    elif c.data == "ite":
        collect_strings_expression(c.children[0])
        collect_strings_commande(c.children[1])
        if len(c.children) > 2:
            collect_strings_commande(c.children[2])
    elif c.data == "skip":
        pass


def generate_data_section(var_decls):
    decl_vars = ""
    for v in var_decls:
        decl_vars += f"{v.value}: dq 0\n"

    string_data = ""
    for label, val in strings.items():
        bytes_repr = ", ".join(str(ord(c)) for c in val)
        string_data += f"{label}: db {bytes_repr}\n"
    return decl_vars + string_data


op2asm = {'+': 'add rax, rbx', '-': 'sub rax, rbx'}

def asm_expression(e):
    if e.data == "string":
        val = e.children[0].value.strip('"')
        label = string_labels[val]
        return f"lea rax, [rel {label}]"

    if e.data == "charat":
        str_code = asm_expression(e.children[0])
        idx_code = asm_expression(e.children[1])
        return f"""{str_code}
push rax
{idx_code}
mov rbx, rax
pop rax
add rax, rbx
movzx rax, byte [rax]
"""

    if e.data == "var":
        return f"mov rax, [{e.children[0].value}]"

    if e.data == "number":
        return f"mov rax, {e.children[0].value}"

    if e.data == "strlen":
        expr = asm_expression(e.children[0])
        return f"""{expr}
mov rdi, rax
call _strlen"""

    if e.data == "char_p":
        return f"mov rax, [{e.children[0].value}]"

    if e.data == "opbin":
        e_left = e.children[0]
        e_op = e.children[1]
        e_right = e.children[2]

        if e_op.value == "+" and any(expr.data in ("string", "char_p", "charat", "strlen", "var") for expr in [e_left, e_right]):
            left_code = asm_expression(e_left)
            right_code = asm_expression(e_right)

            return f"""
; === CONCATENATION START ===
{left_code}
mov rdi, rax
call _strlen
mov rbx, rax
mov r12, rdi

{right_code}
mov rdi, rax
call _strlen
mov rcx, rax
mov r13, rdi

mov rdx, rbx
add rdx, rcx
add rdx, 1           ; +1 pour le caractère nul (\\0)
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
"""

        asm_left = asm_expression(e_left)
        asm_right = asm_expression(e_right)
        return f"""{asm_left}
push rax
{asm_right}
mov rbx, rax
pop rax
{op2asm[e_op.value]}"""

    raise NotImplementedError(f"asm_expression not implemented for {e.data}")


def asm_commande(c):
    global cpt
    if c.data == "affectation":
        return f"{asm_expression(c.children[1])}\nmov [{c.children[0].value}], rax"
    if c.data == "skip":
        return "nop"
    if c.data == "print":
        return f"""{asm_expression(c.children[0])}
mov rdi, fmt_str
mov rsi, rax
xor rax, rax
call printf
"""
    if c.data == "while":
        idx = cpt
        cpt += 1
        return f"""loop{idx}:
{asm_expression(c.children[0])}
cmp rax, 0
jz end{idx}
{asm_commande(c.children[1])}
jmp loop{idx}
end{idx}: nop
"""
    if c.data == "sequence":
        return "\n".join(asm_commande(child) for child in c.children)
    if c.data == "ite":
        idx = cpt
        cpt += 1
        test = asm_expression(c.children[0])
        then_branch = asm_commande(c.children[1])
        else_branch = asm_commande(c.children[2]) if len(c.children) > 2 else ""
        code = f"""{test}
cmp rax, 0
jz else{idx}
{then_branch}
jmp endif{idx}
else{idx}:
{else_branch}
endif{idx}: nop
"""
        return code


def asm_program(p):
    with open("moule.asm") as f:
        prog_asm = f.read()

    collect_strings_commande(p.children[1])
    ret_code = asm_expression(p.children[2])
    prog_asm = prog_asm.replace("RETOUR", ret_code)

    init_vars = ""
    for i, c in enumerate(p.children[0].children):
        init_vars += f"""mov rbx, [argv]
mov rdi, [rbx + {(i+1)*8}]
call atoi
mov [{c.value}], rax
"""

    prog_asm = prog_asm.replace("INIT_VARS", init_vars)
    prog_asm = prog_asm.replace("DECL_VARS", generate_data_section(p.children[0].children))

    body = asm_commande(p.children[1])
    prog_asm = prog_asm.replace("COMMANDE", body)
    return prog_asm


if __name__ == "__main__":
    with open("simple.c") as f:
        src = f.read()
    ast = g.parse(src)
    print(asm_program(ast))
