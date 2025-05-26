from lark import Lark
from context import VariableContext,FunctionContext,GlobalContext

# ══════════════════════════════
# GRAMMAIRE
# ══════════════════════════════

g = Lark(r"""
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9]*/
NUMBER: /[1-9][0-9]*/|"0" 
OPBIN: /[+\-]/
liste_var:                            -> vide
    | IDENTIFIER ("," IDENTIFIER)*    -> vars
liste_expression:                            -> vide
    | expression ("," expression)* -> exprs
expression: IDENTIFIER            -> var
    | expression OPBIN expression -> opbin
    | NUMBER                      -> number
    | IDENTIFIER "(" liste_expression ")" -> call_function_expr
commande: commande (";" commande)*   -> sequence
    | "while" "(" expression ")" "{" commande "}" -> while
    | IDENTIFIER "=" expression              -> affectation
    |"if" "(" expression ")" "{" commande "}" ("else" "{" commande "}")? -> ite
    | "printf" "(" expression ")"                -> print
    | "skip"                                  -> skip
    | "return" "(" expression ")"           -> return
    | IDENTIFIER "(" liste_expression ")" -> call_function_cmd
function: "funct" IDENTIFIER "(" liste_var ")" "{" liste_var commande "}"
program: liste_var function (liste_var function)*
    
%import common.WS
%ignore WS
""", start='program')


# ══════════════════════════════
# ASSEMBLEUR
# ══════════════════════════════

#Compteur pour indexer les boucles et if
cpt = 0

#Association entre opérateurs et code assembleur
op2asm = {'+' : 'add rax, rbx', '-': 'sub rax, rbx'}

#Registres utilisés par convention pour les inputs d'une fonction
registres_input = ["rdi", "rsi", "rdx", "rcx", "r8", "r9"]

#Contexte du programme
global_ctx = GlobalContext()

def asm_expression(e,name_fct):
    """
    Génère le code assembleur d'une expression à partir de son arbre syntaxique.

    Le résultat de l'expression est enregistré dans le registre rax.

    Args:
        e (Tree): L'arbre syntaxique de l'expression.
        name_fct (str): Le nom de la fonction en cours de compilation, utilisé pour 
                         accéder à son contexte local (arguments, variables locales) 
                         dans la structure de définition du programme.

    Returns:
        str: Le code assembleur correspondant à l'expression.
    """

    #Variable
    if e.data == "var": 
        nom_var = e.children[0]

        var_ctx = global_ctx.get_variable(nom_var,name_fct)
        #Vérifie si la variable existe bien d'abord en local puis en global
        if var_ctx.offset :
            return f"mov rax, [rbp - {var_ctx.offset}]"
        return f"mov rax, [{nom_var}]"
        
    
    #Nombre
    if e.data == "number": 
        return f"mov rax, {e.children[0].value}"
    
    #Appel de fonction avec retour
    if e.data == "call_function_expr":
        output = ""
        fct_to_call = e.children[0].value

        #Vérifie que la fonction est bien definie
        if not global_ctx.has_function(fct_to_call):
            raise NameError(f"Fonction non définie : '{fct_to_call}'")
        
        liste_exprs = e.children[1].children

        #Vérifie que l'on appelle bien la fonction avec le bon nombre d'arguments
        if len(liste_exprs) != global_ctx.nb_args(fct_to_call):
            raise TypeError(f"La fonction '{fct_to_call}' attend {global_ctx.nb_args(fct_to_call)} arguments, mais {len(liste_exprs)} ont été fournis.")
        
        #Utilisation d'une pile => On traite les éléments dans le sens inverse
        for expr in reversed(liste_exprs):
            output += asm_expression(expr,name_fct) + "\n"
            output += "push rax\n"
        for i in range(len(liste_exprs)):
            output += f"pop {registres_input[i]}\n"
        output += f"call {fct_to_call}\n"
        return output
    
    #Opération binaire
    if e.data == "opbin":
        e_left = e.children[0]
        e_op = e.children[1]
        e_right = e.children[2]
        asm_left = asm_expression(e_left,name_fct)
        asm_right = asm_expression(e_right,name_fct)
        return f"""{asm_left} 
push rax
{asm_right}
mov rbx, rax
pop rax
{op2asm[e_op.value]}"""
    
    #Erreur si e n'est pas une expression valide
    raise ValueError(f"Type d'expression non pris en charge : {e.data}") 

def asm_commande(c,name_fct):
    """
    Génère le code assembleur d'une commande à partir de son arbre syntaxique.

    Le résultat de la commande est enregistré dans le registre rax.

    Args:
        c (Tree): L'arbre syntaxique de la commande.
        name_fct (str): Le nom de la fonction en cours de compilation, utilisé pour 
                         accéder à son contexte local (arguments, variables locales) 
                         dans la structure de définition du programme.

    Returns:
        str: Le code assembleur correspondant à la commande.
    """

    #Utiliser le compteur global
    global cpt

    #Affectation
    if c.data == "affectation": 
        name_var = c.children[0]
        exp = c.children[1]

        var_ctx = global_ctx.get_variable(name_var,name_fct)
        #Vérifie si la variable existe bien d'abord en local puis en global
        if var_ctx.offset:
            return f"{asm_expression(exp,name_fct)}\nmov [rbp - {var_ctx.offset}], rax"
        return f"{asm_expression(exp,name_fct)}\nmov [{name_var}], rax"
    
    #Skip
    if c.data == "skip": return "nop"
    
    #Print
    if c.data == "print": return f"""{asm_expression(c.children[0],name_fct)}
mov rsi, rax
mov rdi, fmt_int
xor rax, rax
call printf
"""
    
    #While
    if c.data == "while":
        exp = c.children[0]
        body = c.children[1]
        idx = cpt
        cpt += 1
        return f"""loop{idx}:{asm_expression(exp,name_fct)}
cmp rax, 0
jz end{idx}
{asm_commande(body,name_fct)}
jmp loop{idx}
end{idx}: nop
"""
    
    #If et else
    if c.data == "ite":
        output = ""
        exp = c.children[0]
        body_if = c.children[1] 
        idx = cpt
        cpt += 1
        output = f"""if{idx}:{asm_expression(exp,name_fct)}
cmp rax, 0
jz else{idx}
{asm_commande(body_if,name_fct)}
jmp end{idx}
else{idx}: nop
"""
# else{idx}: nop -> car le if n'a pas forcément de else et il doit savoir où sauter
        #S'il y a un else
        if len(c.children) > 2:
            body_else = c.children[2] 
            output += f"{asm_commande(body_else,name_fct)}\n"
        output += f"end{idx}: nop\n"
        return output
    
    #Séquence de commandes
    if c.data == "sequence":
        d = c.children[0]
        tail = c.children[1]
        return f"""{asm_commande(d,name_fct)}
{asm_commande(tail,name_fct)}"""
    
    #Retour de fonction (besoin du label de la fonction pour retourner 
    #au bon endroit du code)
    if c.data == "return": 
        return f"""{asm_expression(c.children[0], name_fct)}
    jmp end_{name_fct}
    """

    #Appel de fonction sans retour
    if c.data == "call_function_cmd":
        output = ""
        fct_to_call = c.children[0].value

        #Vérifie que la fonction est bien definie
        if not global_ctx.has_function(fct_to_call):
            raise NameError(f"Fonction non définie : '{fct_to_call}'")
        
        liste_exprs = c.children[1].children

        #Vérifie que l'on appelle bien la fonction avec le bon nombre d'arguments
        if len(liste_exprs) != global_ctx.nb_args(fct_to_call):
            raise TypeError(f"La fonction {fct_to_call} attend {global_ctx.nb_args(fct_to_call)} arguments, mais {len(liste_exprs)} ont été fournis.")
        
        for expr in reversed(liste_exprs):
            output += asm_expression(expr, name_fct) + "\n"
            output += "push rax\n"
        for i in range(len(liste_exprs)):
            output += f"pop {registres_input[i]}\n"
        output += f"call {fct_to_call}\n"
        return output

    #Erreur si c n'est pas une commande valide
    raise ValueError(f"Type de commande non pris en charge : {c.data}") 

def asm_function(fct):
    """
    Génère le code assembleur d'une fonction à partir de son arbre syntaxique.

    Args:
        fct (Tree): L'arbre syntaxique de la fonction.

    Returns:
        str: Le code assembleur correspondant à la fonction.
    """

    name_fct = fct.children[0].value
    liste_vars_arg = fct.children[1].children
    liste_vars_loc = fct.children[2].children
    commande = fct.children[3]

    output = f"{name_fct}:\n"

    #Initialisation de la pile
    output += f"""push rbp
    mov rbp, rsp
    """
    taille_stack = 8 * (len(liste_vars_arg) + len(liste_vars_loc))
    if taille_stack > 0:
        output += f"sub rsp, {taille_stack}\n"

    i = 0
    #Sauvegarde des arguments
    for var in liste_vars_arg:
        offset = (i+1)*8
        global_ctx.set_offset_arg(var.value,name_fct,offset)
        output += f"mov [rbp - {offset}], {registres_input[i]}\n"
        i += 1

    #Sauvegarde des variables locales
    for var in liste_vars_loc:
        offset = (i+1)*8
        global_ctx.set_offset_local(var.value,name_fct,offset)
        i += 1

    #Exécution les commandes
    output += f"{asm_commande(commande,name_fct)}\n"

    #Nettoyage de la pile
    output += f"""end_{name_fct}:
    mov rsp, rbp
    pop rbp
    ret
    """

    return output

def asm_program(p):
    """
    Génère le code assembleur du programme à partir de son arbre syntaxique.

    Args:
        p (Tree): L'arbre syntaxique du programme.

    Returns:
        str: Le code assembleur correspondant au programme.
    """

    #Moule du programme
    with open("moule.asm") as f:
        prog_asm = f.read()

    #Code assembleur de déclaration des variables globales
    decl_vars = ""

    #Code assembleur d'initialisation des variables globales
    init_vars = ""
    
    #Code assembleur des fonctions (interprété comme COMMANDE)
    asm_f = ""

    #Recherche des variables globales
    for i in range(0, len(p.children), 2):
        vars = p.children[i]
        for var in vars.children:
            #Ajout des variables globales dans la liste des définitions du programme
            global_ctx.add_global(VariableContext(var.value,"int"))

    #Déclaration et initialisation des variables globales
    for i,var in enumerate(global_ctx.globals):
        decl_vars += f"{var}: dq 0\n"
        init_vars += f"""mov rbx, [argv]
mov rdi, [rbx + {(i+1)*8}]
call atoi
mov [{var}], rax
"""
    prog_asm = prog_asm.replace("INIT_VARS", init_vars)
    prog_asm = prog_asm.replace("DECL_VARS", decl_vars)

    #Définition des fonctions
    for i in range(1, len(p.children), 2):
        fct = p.children[i]

        #Cas particulier pour la fonction main : on l'écrit au début pour commencer
        #par cette dernière
        if fct.children[0].value == "main":
            fct.children[0].value = "main_function"
            prog_asm = prog_asm.replace("CALL_MAIN", "call main_function")

        name_fct = fct.children[0].value

        #Pour faire en sorte que l'ordre d'implémentation de fonctions n'est pas 
        #d'importance
        liste_args = fct.children[1].children
        liste_locals = fct.children[2].children

        fct_ctx = FunctionContext(name_fct)
        for arg in liste_args :
            fct_ctx.add_arg(VariableContext(arg.value,"int"))
        for local in liste_locals :
            fct_ctx.add_local(VariableContext(local.value,"int"))
        global_ctx.add_function(fct_ctx)

    #Compilation des fonctions
    for i in range(1, len(p.children), 2):
        asm_f += f"{asm_function(p.children[i])}\n"
    
    prog_asm = prog_asm.replace("COMMANDE", asm_f)
    return prog_asm 


# ══════════════════════════════
# AFFICHAGE
# ══════════════════════════════


def pp_expression(e):
    """
    Génère une représentation lisible (pretty-print) d'une expression à partir de son arbre syntaxique.

    Args:
        e (Tree): L'arbre syntaxique représentant l'expression.

    Returns:
        str: La représentation textuelle lisible de l'expression.
    """

    #Variable et nombre
    if e.data in ("var","number"): return f"{e.children[0].value}"

    #Appel de fonction avec retour
    if e.data == "call_function_expr":
        name = e.children[0]
        liste_exprs = ""
        for expr in e.children[1].children:
            liste_exprs += expr + ","
        return f"{name}({liste_exprs[:-1]})"
    
    #Opération binaire
    if e.data == "opbin":
        e_left = e.children[0]
        e_op = e.children[1]
        e_right = e.children[2]
        return f"{pp_expression(e_left)} {e_op.value} {pp_expression(e_right)}"
    
    #Erreur si e n'est pas une expression valide
    raise ValueError(f"Type d'expression non pris en charge : {e.data}") 

def pp_commande(c):
    """
    Génère une représentation lisible (pretty-print) d'une commande à partir de son arbre syntaxique.

    Args:
        e (Tree): L'arbre syntaxique représentant la commande.

    Returns:
        str: La représentation textuelle lisible de la commande.
    """

    #Affectation
    if c.data == "affectation": 
        var = c.children[0]
        exp = c.children[1]
        return f"{var.value} = {pp_expression(exp)}"
    
    #Skip
    if c.data == "skip": return "skip"

    #Print
    if c.data == "print": return f"printf({pp_expression(c.children[0])})"

    #While
    if c.data == "while":
        exp = c.children[0]
        body = c.children[1]
        return f"while ( {pp_expression(exp)} ) {{{pp_commande(body)}}}"
    
    # If et Else
    if c.data == "ite":
        exp = c.children[0]
        body_if = c.children[1]
        output = f"""if ({pp_expression(exp)}) {{
        {pp_commande(body_if)}
    }}"""
        if len(c.children) > 2:
            body_else = c.children[2]
            output += f""" else {{
        {pp_commande(body_else)}
    }}"""
        return output

    
    #Séquence de commandes
    if c.data == "sequence":
        d = c.children[0]
        tail = c.children[1]
        return f"""{pp_commande(d)} ;
    {pp_commande(tail)}"""

    #Retour de fonction
    if c.data == "return":
        return f"return ({pp_expression(c.children[0])})"
    
    #Appel de fonction sans retour
    if c.data == "call_function_cmd":
        name = c.children[0]
        liste_exprs = ""
        for expr in c.children[1].children:
            liste_exprs += pp_expression(expr) + ","
        return f"{name}({liste_exprs[:-1]})"
    
    #Erreur si c n'est pas une expression valide
    raise ValueError(f"Type de commande non pris en charge : {c.data}") 

def pp_function(f):
    """
    Génère une représentation lisible (pretty-print) d'une fonction à partir de son arbre syntaxique.

    Args:
        e (Tree): L'arbre syntaxique représentant la fonction.

    Returns:
        str: La représentation textuelle lisible de la fonction.
    """
    name = f.children[0]
    liste_args = ""
    for arg in f.children[1].children:
        liste_args += arg + ","
    liste_args = liste_args[:-1]
    liste_locs = ""
    for var in f.children[1].children:
        liste_locs += var + ","
    liste_locs = liste_locs[:-1]
    c2 = f.children[3]
    return f"""funct {name} ({liste_args}){{
    {liste_locs}
    {pp_commande(c2)}
}}"""

def pp_program(p):
    """
    Génère une représentation lisible (pretty-print) du programme à partir de son arbre syntaxique.

    Args:
        e (Tree): L'arbre syntaxique représentant le programme.

    Returns:
        str: La représentation textuelle lisible du programme.
    """
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
    
    #Ouverture du programme d'un fichier externe
    with open("simple.c") as f:
        src = f.read()

    #Arbre syntaxique du programme
    ast = g.parse(src)

    #Affichage du code assembleur du programme
    print(asm_program(ast))