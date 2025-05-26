from lark import Lark

cpt = 0
last_stack_variable = 0

""" For the implementation of static types, I decided to

"""


g = Lark(
    """
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9]*/
TYPE: "int"|"double"|"char"|"bool"|"long"
NUMBER: /[1-9][0-9]*/|"0"
OPBIN: /[+\-*\/>]/
liste_var:                            -> vide
    | IDENTIFIER ("," IDENTIFIER)*    -> vars
expression: IDENTIFIER            -> var
    | expression OPBIN expression -> opbin
    | NUMBER                      -> number
commande: commande (";" commande)*   -> sequence
    | "while" "(" expression ")" "{" commande "}" -> while
    | IDENTIFIER "=" expression              -> affectation
    | TYPE IDENTIFIER "=" expression -> declaration
|"if" "(" expression ")" "{" commande "}" ("else" "{" commande "}")? -> ite
| "printf" "(" expression ")"                -> print
| "skip"                                  -> skip
program:"main" "(" liste_var ")" "{"commande"return("expression")" "}"
%import common.WS
%ignore WS
""",
    start="program",
)


def get_vars_expression(e):
    pass


def get_vars_commande(c):
    pass


op2asm = {"+": "add rax, rbx", "-": "sub rax, rbx"}
variables_adresses = {}
var_size = {"int": 4, "double": 8, "char": 8, "bool": 8, "long": 8}
register = {"1": "al", "2": "ax", "4": "eax", "8": "rax"}


def asm_expression(e):
    if e.data == "var":
        needed_bytes = str(variables_adresses[e.children[0]][1])
        return (
            f"mov {register[needed_bytes]}, [rbp{variables_adresses[e.children[0]][0]}]"
        )
    if e.data == "number":
        return f"mov rax, {e.children[0]}"
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


def transfo_int_number(s):
    if s == "int" or s == "double" or s == "long":
        return "NUMBER"
    return s


def type_of_expression(e):
    if e.data == "number":
        return "int"
    if e.data == "var":
        return variables_adresses[e.children[0].value][2]
    if e.data == "opbin":
        e_left = e.children[0]
        e_right = e.children[2]
        type_left_exp = type_of_expression(e_left)
        type_right_exp = type_of_expression(e_right)
        if type_left_exp != type_right_exp:
            raise TypeError(
                f"Expression of the left {e_left} is not the same type as the one on the right {e_right}"
            )
        return type_of_expression(e_left)


def asm_commande(c):
    global last_stack_variable
    global cpt
    if c.data == "declaration":
        type_var = c.children[0]
        var = c.children[1]
        exp = c.children[2]
        size = var_size[type_var]
        last_stack_variable -= size
        variables_adresses[var] = (last_stack_variable, size, type_var.value)
        needed_bytes = str(register[str(size)])
        return f"""
sub rsp, {size}
{asm_expression(exp)}
mov [rbp{last_stack_variable}], {needed_bytes}
"""
    if c.data == "affectation":
        var = c.children[0]
        exp = c.children[1]
        # Check for declaration before affectation
        if var not in variables_adresses:
            raise Exception(f"Undefined variable {var}")
        if type_of_expression(exp) != variables_adresses[var][2]:
            raise TypeError(f"Expression {exp} is not the same type as {var}")

        needed_bytes = str(register[str(variables_adresses[var.value][1])])

        return f"""
{asm_expression(exp)}
mov [rbp{variables_adresses[var.value][0]}], {needed_bytes}
"""

    if c.data == "skip":
        return "nop"
    if c.data == "print":
        return f"""{asm_expression(c.children[0])}
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
        return f"""
loop{idx}: {asm_expression(exp)}
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
    asm_c = asm_commande(p.children[1])
    ret = asm_expression(p.children[2])
    prog_asm = prog_asm.replace("RETOUR", ret)
    init_vars = ""
    decl_vars = ""
    for i, c in enumerate(p.children[0].children):
        init_vars += f"""mov rbx, [argv]
mov rdi, [rbx + {(i + 1) * 8}]
call atoi
mov[{c.value}], rax
"""
        decl_vars += f"{c.value}: dq 0\n"
    prog_asm = prog_asm.replace("INIT_VARS", init_vars)
    prog_asm = prog_asm.replace("DECL_VARS", decl_vars)
    prog_asm = prog_asm.replace("COMMANDE", asm_c)
    prog_asm = prog_asm.replace("VIDE_MEMOIRE", f"add rsp, {-last_stack_variable}")
    return prog_asm


def pp_expression(e):
    if e.data in ("var", "number"):
        return f"{e.children[0].value}"
    e_left = e.children[0]
    e_op = e.children[1]
    e_right = e.children[2]
    return f"{pp_expression(e_left)} {e_op.value} {pp_expression(e_right)}"


def pp_commande(c):
    if c.data == "declaration":
        type_var = c.children[0]
        var = c.children[1]
        exp = c.children[2]
        return f"{type_var} {var.value} = {pp_expression(exp)}"
    if c.data == "affectation":
        var = c.children[0]
        exp = c.children[1]
        return f"{var.value} = {pp_expression(exp)}"
    if c.data == "skip":
        return "skip"
    if c.data == "print":
        return f"printf({pp_expression(c.children[0])})"
    if c.data == "while":
        exp = c.children[0]
        body = c.children[1]
        return f"while ( {pp_expression(exp)} ) {{{pp_commande(body)}}}"
    if c.data == "sequence":
        d = c.children[0]
        tail = c.children[1]
        return f"{pp_commande(d)} ; {pp_commande(tail)}"


if __name__ == "__main__":
    with open("simple.c") as f:
        src = f.read()
    ast = g.parse(src)
    # print(pp_commande(ast))
    print(asm_program(ast))
    # print(var_size)
    # print(ast)
    # print(ast.children[1])
    # print(ast.children[0])
    # print(pp_commande(ast.children[1]))
# print(ast.children)
# print(ast.children[0].type)
# print(ast.children[0].value)
