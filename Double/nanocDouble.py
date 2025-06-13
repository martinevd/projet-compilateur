from lark import Lark

import struct


cpt = 0
g = Lark(r"""
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9]*/
INTEGER: /[1-9][0-9]*/|"0" 
DOUBLE: /[1-9][0-9]*\.[0-9]+/|/0\.[0-9]+/
OPBIN: /[+\-*\/>]/
liste_var:                            -> vide
    | IDENTIFIER ("," IDENTIFIER)*    -> vars
expression: IDENTIFIER            -> var
    | expression OPBIN expression -> opbin
    | INTEGER                     -> int
    | DOUBLE                      -> double
commande: commande (";" commande)*   -> sequence
    | "while" "(" expression ")" "{" commande "}" -> while
    | IDENTIFIER "=" expression              -> affectation
|"if" "(" expression ")" "{" commande "}" ("else" "{" commande "}")? -> ite
| "printf" "(" expression ")"                -> print
| "skip"                                  -> skip
program:"main" "(" liste_var ")" "{" commande "return" "(" expression ")" "}"
%import common.WS
%ignore WS
""", start='program')

# voir pour transformer:
#       NUMBER: /[1-9][0-9]*\.[0-9]+/|/0\.[0-9]+/|/[1-9][0-9]*/|"0" 
# en:
#       INT: /[1-9][0-9]*/|"0" 
#       FLOAT: /[1-9][0-9]*\.[0-9]+/|/0\.[0-9]+/

def get_vars_expression(e):
    pass

def get_vars_commande(c):
    pass

op2asm = {'+' : 'add rax, rbx', '-': 'sub rax, rbx'}
op2asmDouble = {'+' : 'addsd xmm0, xmm1', '-': 'subsd xmm0, xmm1'}

float_constants = {}
float_count = 0

def asm_expression(e):
    global float_count
    if e.data == "var": 
        return f"mov rax, [{e.children[0].value}]"
    if e.data == "int": 
        return f"mov rax, {e.children[0].value}"
    if e.data == "double": 
        value_double = e.children[0].value
        label = float_constants.get(value_double)
        if label is None:
            label = f"LC{float_count}"
            float_constants[value_double] = label
            float_count += 1
        return f"movsd xmm0, [{label}]"
    
    if e.data == "opbin":
        e_left = e.children[0]
        e_op = e.children[1]
        e_right = e.children[2]
        if e_left.data == "int":
            asm_left = asm_expression(e_left)
            asm_right = asm_expression(e_right)
            return f"""{asm_left} 
push rax
{asm_right}
mov rbx, rax
pop rax
{op2asm[e_op.value]}"""
        if e_left.data == "double":
            asm_left = asm_expression(e_left)
            asm_right = asm_expression(e_right)
            return f"""{asm_left} 
sub rsp, 8
movsd [rsp], xmm0
{asm_right}
movsd xmm1, xmm0
movsd xmm0, [rsp]
add rsp, 8
{op2asmDouble[e_op.value]}"""
    

def asm_commande(c):
    global cpt

    if c.data == "affectation": 
        var = c.children[0]
        exp = c.children[1]
        code = asm_expression(exp)
        if exp.data == "double" or exp.data == "opbin":
            return f"""{code}
movsd [{var.value}], xmm0"""
        else:
            return f"""{code}
mov [{var.value}], rax"""
        
    if c.data == "skip": return "nop"

    if c.data == "print":
        exp = c.children[0]
        code = asm_expression(exp)
        if exp.data == "double": #gérer les print si c'est des double
            return f"""{code}
mov rdi, fmt_double
xor rax, rax
call printf"""
        else:
            return f"""{asm_expression(c.children[0])}
mov rsi, fmt_int
mov rdi, rax
xor rax, rax
call printf
"""
    if c.data == "while":
        exp = c.children[0]
        body = c.children[1]
        idx = cpt
        cpt += 1
        return f"""loop{idx}:{asm_expression(exp)}
cmp rax, 0
jz end{idx}
{asm_commande(body)}
jmp loop{idx}
end{idx}: nop
"""
    if c.data == "sequence":
        d = c.children[0]
        tail = c.children[1]
        return f"{asm_commande(d)}\n {asm_commande(tail)}"
    

def asm_program(p):
    with open("mouleDouble.asm") as f:
        prog_asm = f.read()

    asm_c = asm_commande(p.children[1])

    data_doubles = ""
    for val, label in float_constants.items():
        b = struct.unpack("<Q", struct.pack("<d", float(val)))[0]
        data_doubles += f"{label}: dq 0x{b:016x}\n"

    ret = asm_expression(p.children[2])
    prog_asm = prog_asm.replace("RETOUR", ret)
    
    init_vars = ""
    decl_vars = ""
    for i, c in enumerate(p.children[0].children):
        init_vars += f"""mov rbx, [argv]
mov rdi, [rbx + {(i+1)*8}]
call atoi
mov [{c.value}], rax
"""
        decl_vars += f"{c.value}: dq 0\n"   #déclaration des variables

    # Ajoute les constantes doubles ici, après avoir collecté float_constants
    prog_asm = prog_asm.replace("DECL_VARS", decl_vars + data_doubles)
    prog_asm = prog_asm.replace("INIT_VARS", init_vars)
    prog_asm = prog_asm.replace("COMMANDE", asm_c)
    return prog_asm


def pp_expression(e):
    if e.data in ("var","int"): return f"{e.children[0].value}"
    e_left = e.children[0]
    e_op = e.children[1]
    e_right = e.children[2]
    return f"{pp_expression(e_left)} {e_op.value} {pp_expression(e_right)}"

def pp_commande(c):
    if c.data == "affectation": 
        var = c.children[0]
        exp = c.children[1]
        return f"{var.value} = {pp_expression(exp)}"
    if c.data == "skip": return "skip"
    if c.data == "print": return f"printf({pp_expression(c.children[0])})"
    if c.data == "while":
        exp = c.children[0]
        body = c.children[1]
        return f"while ( {pp_expression(exp)} ) {{{pp_commande(body)}}}"
    if c.data == "sequence":
        d = c.children[0]
        tail = c.children[1]
        return f"{pp_commande(d)} ; {pp_commande(tail)}"
    

if __name__ == "__main__":
    with open("simpleDouble.c") as f:
        src = f.read()
    ast = g.parse(src)
    print(asm_program(ast))

    #print(pp_expression(3.14))
    
    #print(pp_commande(ast))
    #print(asm_program(ast))
    #print(pp_commande(ast))
    #print(ast.children)
    #print(ast.children[0].type)
    #print(ast.children[0].value)
