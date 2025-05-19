from lark import Lark, Tree

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
    | "return" "(" expression ")"           -> return
function: "funct" IDENTIFIER "(" liste_var ")" "{" commande "}"
program: liste_var function (liste_var function)*
    
%import common.WS
%ignore WS
""", start='program')

op2asm = {'+' : 'add rax, rbx', '-': 'sub rax, rbx'}
def asm_expression(e,var_locales):
    if e.data == "var": 
        var = e.children[0]
        if var.value in var_locales:
            return f"mov rax, [rbp - {var_locales[var.value]}]"
        return f"mov rax, [{var.value}]"
    if e.data == "number": 
        return f"mov rax, {e.children[0].value}"
    if e.data == "call_function":
        output = ""
        for var in reversed(e.children[1].children):
            var_tree = Tree("var", [var])
            output += asm_expression(var_tree,var_locales) + "\n"
            output += "push rax\n"
        registres_input = ["rdi", "rsi", "rdx", "rcx", "r8", "r9"]
        for i in range(len(e.children[1].children)):
            output += f"pop {registres_input[i]}\n"
        output += f"call {e.children[0].value}\n"
        return output
    e_left = e.children[0]
    e_op = e.children[1]
    e_right = e.children[2]
    asm_left = asm_expression(e_left,var_locales)
    asm_right = asm_expression(e_right,var_locales)
    return f"""{asm_left} 
push rax
{asm_right}
mov rbx, rax
pop rax
{op2asm[e_op.value]}"""

def asm_commande(c,var_locales,label_funct=""):
    global cpt
    if c.data == "affectation": 
        var = c.children[0]
        exp = c.children[1]
        if var.value in var_locales :
            return f"{asm_expression(exp,var_locales)}\nmov [rbp - {var_locales[var.value]}], rax"
        return f"{asm_expression(exp,var_locales)}\nmov [{var.value}], rax"
    if c.data == "skip": return "nop"
    if c.data == "print": return f"""{asm_expression(c.children[0],var_locales)}
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
        return f"""loop{idx}:{asm_expression(exp,var_locales)}
cmp rax, 0
jz end{idx}
{asm_commande(body,var_locales,label_funct)}
jmp loop{idx}
end{idx}: nop
"""
    if c.data == "sequence":
        d = c.children[0]
        tail = c.children[1]
        return f"""{asm_commande(d,var_locales,label_funct)}
{asm_commande(tail,var_locales,label_funct)}"""
    if c.data == "return": 
        return f"""{asm_expression(c.children[0],var_locales)}
    jmp end_{label_funct}
    """

def asm_function(fct):
    nom_fct = fct.children[0].value
    liste_vars = fct.children[1].children
    commande = fct.children[2]

    output = f"{nom_fct}:\n"

    #Initiation pile
    output += f"""push rbp
    mov rbp, rsp
    """
    taille_stack = 8 * len(liste_vars)
    if taille_stack > 0:
        output += f"sub rsp, {taille_stack}\n"

    #Variables
    registres_input = ["rdi", "rsi", "rdx", "rcx", "r8", "r9"]
    var_locales = {}
    for i,var in enumerate(liste_vars):
        offset = (i+1) * 8
        var_locales[var.value] = offset
        output += f"mov [rbp - {offset}], {registres_input[i]}\n"

    #Faire les commandes
    output += f"{asm_commande(commande,var_locales,nom_fct)}\n"

    #Nettoyage pile
    output += f"""end_{nom_fct}:
    mov rsp, rbp
    pop rbp
    ret
    """

    return output

def asm_program(p):
    with open("moule.asm") as f:
        prog_asm = f.read()
    init_vars = ""
    decl_vars = ""
    asm_c = ""

    #Variables globales
    global_vars = []
    for i in range(0, len(p.children), 2):
        vars = p.children[i]
        for var in vars.children:
            global_vars.append(var.value)

    for i,var in enumerate(global_vars):
        decl_vars += f"{var}: dq 0\n"
        init_vars += f"""mov rbx, [argv]
mov rdi, [rbx + {(i+1)*8}]
call atoi
mov [{var}], rax
"""
    prog_asm = prog_asm.replace("INIT_VARS", init_vars)
    prog_asm = prog_asm.replace("DECL_VARS", decl_vars)

    #Commandes
    for i in range(1, len(p.children), 2):
        fct = p.children[i]

        if fct.children[0].value == "main":
            fct.children[0].value = "main_function"
            prog_asm = prog_asm.replace("CALL_MAIN", "call main_function")

        asm_c += f"{asm_function(fct)}\n"
    
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
        return f"""{pp_commande(d)} ;
    {pp_commande(tail)}"""
    if c.data == "return":
        return f"return ({pp_expression(c.children[0])})"

def pp_function(f):
    name = f.children[0]
    liste_vars = ""
    for var in f.children[1].children:
        liste_vars += var + ","
    liste_vars = liste_vars[:-1]
    c2 = f.children[2]
    return f"""funct {name} ({liste_vars}){{
    {pp_commande(c2)}
}}"""

def pp_program(p):
    output = ""
    for i in range(0, len(p.children), 2):
        vars = p.children[i]
        fct = p.children[i+1]
        liste_vars =""
        for var in vars.children:
            liste_vars += var + ", "
        liste_vars = liste_vars[:-2]
        output += f"{liste_vars}\n{pp_function(fct)}\n"
    return output


if __name__ == "__main__":
    with open("simple.c") as f:
        src = f.read()
    ast = g.parse(src)
    print(asm_program(ast))