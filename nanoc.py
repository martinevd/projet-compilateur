from lark import Lark

cpt = 0
g = Lark(r"""
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9]*/
NUMBER: /[1-9][0-9]*/|"0" 
OPBIN: /[+\-]/
liste_var:                            -> vide
    | IDENTIFIER ("," IDENTIFIER)*    -> vars
expression: IDENTIFIER            -> var
    | expression OPBIN expression -> opbin
    | NUMBER                      -> number
    | IDENTIFIER "(" liste_var ")" -> call_function
commande: commande (";" commande)*   -> sequence
    | "while" "(" expression ")" "{" commande "}" -> while
    | IDENTIFIER "=" expression              -> affectation
    |"if" "(" expression ")" "{" commande "}" ("else" "{" commande "}")? -> ite
    | "printf" "(" expression ")"                -> print
    | "skip"                                  -> skip
function: "funct" IDENTIFIER "(" liste_var ")" "{" commande "return" "(" expression ")" "}"
program: function (function)*
%import common.WS
%ignore WS
""", start='function')

op2asm = {'+' : 'add rax, rbx', '-': 'sub rax, rbx'}
def asm_expression(e):
    if e.data == "var": return f"mov rax, [{e.children[0].value}]"
    if e.data == "number": return f"mov rax, {e.children[0].value}" 
    e_left = e.children[0]
    e_op = e.children[1]
    e_right = e.children[2]
    asm_left = asm_expression(e_left)
    asm_right = asm_expression(e_right)
    return f"""{asm_left} 
push rax
{asm_right}
mov rbx, rax
pop rax
{op2asm[e_op.value]}"""

def asm_commande(c):
    global cpt
    if c.data == "affectation": 
        var = c.children[0]
        exp = c.children[1]
        return f"{asm_expression(exp)}\nmov [{var.value}], rax"
    if c.data == "skip": return "nop"
    if c.data == "print": return f"""{asm_expression(c.children[0])}
mov rsi, fmt
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
    with open("moule.asm") as f:
        prog_asm = f.read()
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
        decl_vars += f"{c.value}: dq 0\n"
    prog_asm = prog_asm.replace("INIT_VARS", init_vars)
    prog_asm = prog_asm.replace("DECL_VARS", decl_vars)
    asm_c = asm_commande(p.children[1])
    prog_asm = prog_asm.replace("COMMANDE", asm_c)
    return prog_asm    

def pp_expression(e):
    if e.data in ("var","number"): return f"{e.children[0].value}"
    if e.data == "call_function":
        name = e.children[0]
        liste_vars = ""
        for var in e.children[1].children:
            liste_vars += var + ","
        if len(liste_vars) > 0 : liste_vars = liste_vars[:-1]
        return f"{name}({liste_vars})"
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

def pp_function(f):
    name = f.children[0]
    liste_vars = ""
    for var in f.children[1].children:
        liste_vars += var + ","
    if len(liste_vars) > 0 : liste_vars = liste_vars[:-1]
    c2 = f.children[2]
    exp = f.children[3]
    return f"""funct {name} ({liste_vars}){{
    {pp_commande(c2)}
    return ({pp_expression(exp)})
}}"""




if __name__ == "__main__":
    """
    with open("simple.c") as f:
        src = f.read()
    ast = g.parse(src)
    print(asm_program(ast))
    """

    src = "funct maFonction(X,Y) {X = maFonction2(Y) return(X)}"
    ast = g.parse(src)
    print(pp_function(ast))
