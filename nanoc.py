from lark import Lark
from context import VariableContext,FunctionContext,GlobalContext

# ══════════════════════════════
# GRAMMAIRE
# ══════════════════════════════

g = Lark(r"""
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9]*/
TYPE: "int"|"double"|"string"|"char"
NUMBER: /[1-9][0-9]*/|"0" 
OPBIN: /[+\-]/
STRING: "\"" /[^\"]*/ "\""
decl_var : TYPE IDENTIFIER
liste_decl_var:                            -> vide
    |  decl_var ("," decl_var)*    -> vars
liste_expression:                            -> vide
    | expression ("," expression)* -> exprs
expression: IDENTIFIER            -> var
    | expression OPBIN expression -> opbin
    | NUMBER                      -> number
    | STRING                      -> string
    | "len" "(" expression ")"    -> strlen
    | expression "[" expression "]"  -> charat  
    | IDENTIFIER "(" liste_expression ")" -> call_function_expr
commande: commande (";" commande)*   -> sequence
    | "while" "(" expression ")" "{" commande "}" -> while
    | IDENTIFIER "=" expression              -> affectation
    | TYPE IDENTIFIER ("=" expression)? -> declaration
    |"if" "(" expression ")" "{" commande "}" ("else" "{" commande "}")? -> ite
    | "printf" "(" expression ")"                -> print
    | "skip"                                  -> skip
    | "return" "(" expression ")"           -> return
    | IDENTIFIER "(" liste_expression ")" -> call_function_cmd
function: ("void"|TYPE) IDENTIFIER "(" liste_decl_var ")" "{" commande "}"
program: liste_decl_var function (liste_decl_var function)*
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

   
def type_of_expression(e,name_fct):
    if e.data == "number":
        return "int"
    if e.data == "string":
        return "string"
    if e.data == "var":
        var_ctx = global_ctx.get_variable(e.children[0],name_fct)
        return var_ctx.var_type
    if e.data == "opbin":
        e_left = e.children[0]
        e_right = e.children[2]
        type_left_exp = type_of_expression(e_left,name_fct)
        type_right_exp = type_of_expression(e_right,name_fct)
        if type_left_exp != type_right_exp:
            raise TypeError(
                f"Expression of the left {e_left} is not the same type as the one on the right {e_right}"
            )
        return type_of_expression(e_left,name_fct)
    if e.data == "call_function_expr":
        fct_to_call = global_ctx.get_function(e.children[0].value)
        return fct_to_call.return_type
    if e.data == "strlen":
        return "int"
    if e.data == "charat":
        return "char"
    
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
        var_ctx = global_ctx.get_variable(e.children[0],name_fct)
        #Vérifie si la variable existe bien d'abord en local puis en global
        if var_ctx.offset :
            return f"mov rax, [rbp - {var_ctx.offset}]"
        return f"mov rax, [{var_ctx.name}]"
    
    #Nombre
    if e.data == "number":
        return f"mov rax, {e.children[0].value}"
    
    #String
    if e.data == "string":
        string_val = e.children[0].value.strip('"')
        label = global_ctx.label_string(string_val)
        return f"lea rax, [rel {label}]"
    
    #Len
    if e.data == "strlen":
        expr = e.children[0]
        if type_of_expression(expr,name_fct) != "string":
            raise TypeError(f"La méthode str_len ne peut être utilisée que sur des chaînes de caractères, pas sur une expression de type {type_of_expression(expr)}.")
        return f"""{asm_expression(e.children[0], name_fct)}
mov rdi, rax
call strlen"""
    
    #Charat
    if e.data == "charat":
        asm_str = asm_expression(e.children[0], name_fct) 
        asm_index = asm_expression(e.children[1], name_fct)  
        return f"""
{asm_str}         
push rax
{asm_index}       
mov rbx, rax        
pop rax           
add rax, rbx        
movzx rax, byte [rax]  
"""
    
    # Appel de fonction avec retour
    if e.data == "call_function_expr":
        output = ""
        fct_to_call = e.children[0].value

        # Vérifie que la fonction est bien définie
        if not global_ctx.has_function(fct_to_call):
            raise NameError(f"Fonction non définie : '{fct_to_call}'")
        
        liste_exprs = e.children[1].children
        fct_ctx = global_ctx.get_function(fct_to_call)
        
        if len(liste_exprs) != global_ctx.nb_args(fct_to_call):
            raise TypeError(f"La fonction '{fct_to_call}' attend {global_ctx.nb_args(fct_to_call)} arguments, mais {len(liste_exprs)} ont été fournis.")
        
        # Push les arguments (en inversé pour pile)
        for expr in reversed(liste_exprs):
            output += asm_expression(expr, name_fct) + "\n"
            output += "push rax\n"

        arg_names = list(fct_ctx.args.keys())
        # Pop dans les bons registres en fonction du type
        for i, expr in enumerate(liste_exprs):
            output += f"pop {registres_input[i]}\n"

        output += f"call {fct_to_call}\n"
        return output

    
    #Opération binaire
    # Opération binaire
    if e.data == "opbin":
        e_left = e.children[0]
        e_op = e.children[1]
        e_right = e.children[2]
        
        type_left = type_of_expression(e_left, name_fct)
        type_right = type_of_expression(e_right, name_fct)

        # Cas particulier pour la concaténation de strings
        if e_op.value == "+" and type_left == "string" and type_right == "string":
            asm_left = asm_expression(e_left, name_fct)    # rax = addr str1
            asm_right = asm_expression(e_right, name_fct)  # rax = addr str2

            return f"""
{asm_left}
push rax              
{asm_right}
pop rdi               
mov rsi, rax          
call concat_strings  
"""
        else:
            # cas général : entier
            asm_left = asm_expression(e_left, name_fct)
            asm_right = asm_expression(e_right, name_fct)
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
    

    #Declaration
    if c.data == "declaration":

        fct_ctx = global_ctx.get_function(name_fct)

        var_name = c.children[1].value
        var_type = c.children[0].value
        offset = fct_ctx.last_offset + 8

        fct_ctx.add_local(VariableContext(var_name,var_type,offset,name_fct))
        fct_ctx.last_offset += 8

        if (len(c.children) > 2):
            exp = c.children[2]
            return f"""sub rsp, 8
{asm_expression(exp, name_fct)}
mov [rbp - {offset}], rax
"""
        return f"sub rsp, 8"

    #Affectation
    if c.data == "affectation":
        name_var = c.children[0].value
        exp = c.children[1]
          
        var_ctx = global_ctx.get_variable(name_var,name_fct)      

        if type_of_expression(exp,name_fct) != var_ctx.var_type:
            raise TypeError(f"Expression {exp} is not the same type as {name_var}")

        #Vérifie si la variable existe bien d'abord en local puis en global
        if var_ctx.offset:
            return f"""{asm_expression(exp,name_fct)}
mov [rbp - {var_ctx.offset}], rax"""
        return f"""{asm_expression(exp,name_fct)}
mov [{name_var}], rax"""
    
    #Skip
    if c.data == "skip": return "nop"
    
    #Print
    if c.data == "print":
        type_exp = type_of_expression(c.children[0], name_fct)
        
        if type_exp == "string":
            fmt = "fmt_str"
        elif type_exp == "char":
            fmt = "fmt_char"    
        else:
            fmt = "fmt_int"
        return f"""{asm_expression(c.children[0],name_fct)}
mov rsi, rax
mov rdi, {fmt}
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
        exp = c.children[0]
        type_exp = type_of_expression(exp,name_fct)
        fct_ctx = global_ctx.get_function(name_fct)
        
        if (type_exp != fct_ctx.return_type):
            raise TypeError(
            f"La fonction '{name_fct}' doit retourner un(e)'{fct_ctx.return_type}', "
            f"mais retourne un(e)'{type_exp}'"
        ) 

        return f"""{asm_expression(exp, name_fct)}
    jmp end_{name_fct}
    """

    # Appel de fonction sans retour
    if c.data == "call_function_cmd":
        output = ""
        fct_to_call = c.children[0].value

        if not global_ctx.has_function(fct_to_call):
            raise NameError(f"Fonction non définie : '{fct_to_call}'")
        
        liste_exprs = c.children[1].children
        fct_ctx = global_ctx.get_function(fct_to_call)

        if len(liste_exprs) != global_ctx.nb_args(fct_to_call):
            raise TypeError(f"La fonction {fct_to_call} attend {global_ctx.nb_args(fct_to_call)} arguments, mais {len(liste_exprs)} ont été fournis.")
        
        for expr in reversed(liste_exprs):
            output += asm_expression(expr, name_fct) + "\n"
            output += "push rax\n"

        arg_names = list(fct_ctx.args.keys())
        for i, expr in enumerate(liste_exprs):
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

    has_type = len(fct.children) == 4

    type_offset = 1 if has_type else 0

    name_fct = fct.children[type_offset].value
    liste_vars_arg = fct.children[type_offset + 1].children
    commande = fct.children[type_offset + 2]

    output = f"{name_fct}:\n"

    #Initialisation de la pile
    output += f"""push rbp
    mov rbp, rsp
    """
    #Sauvegarde des arguments
    for i,decl_var in enumerate(liste_vars_arg):
        type_var = decl_var.children[0].value
        name_var = decl_var.children[1].value

        var_ctx = global_ctx.get_variable(name_var,name_fct)
        output += f"""sub rsp, 8
mov [rbp - {var_ctx.offset}], {registres_input[i]}
"""

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

    # Ajoute les chaînes en .data
    decl_strings = ""

    #Recherche des variables globales
    for i in range(0, len(p.children), 2):
        vars = p.children[i]
        for decl_var in vars.children:
            type_var = decl_var.children[0].value
            name_var = decl_var.children[1].value

            #Ajout des variables globales dans la liste des définitions du programme
            global_ctx.add_global(VariableContext(name_var,type_var))

    #Déclaration et initialisation des variables globales
    for i,var in enumerate(global_ctx.globals):
        decl_vars += f"{var}: dq 0\n"
        init_vars += f"""mov rbx, [argv]
mov rdi, [rbx + {8 * (i + 1)}]
call atoi
mov [{var}], rax
"""

    prog_asm = prog_asm.replace("INIT_VARS", init_vars)
    prog_asm = prog_asm.replace("DECL_VARS", decl_vars)

    #Définition des fonctions
    for i in range(1, len(p.children), 2):
        fct = p.children[i]

        has_type = len(fct.children) == 4
        type_offset = 1 if has_type else 0

        return_type = fct.children[0].value if has_type else "void"
        name_fct = fct.children[type_offset].value
        liste_vars_arg = fct.children[type_offset + 1].children

        #Cas particulier pour la fonction exec : on l'écrit au début pour commencer
        #par cette dernière
        if name_fct == "exec":
            prog_asm = prog_asm.replace("CALL_EXEC", "call exec")

        #Pour faire en sorte que l'ordre d'implémentation de fonctions n'est pas 
        #d'importance

        fct_ctx = FunctionContext(name_fct,return_type)
        for decl_arg in liste_vars_arg :
            type_arg = decl_arg.children[0].value
            name_arg = decl_arg.children[1].value

            offset = fct_ctx.last_offset + 8
            
            fct_ctx.add_arg(VariableContext(name_arg,type_arg,offset))
        global_ctx.add_function(fct_ctx)

    #Compilation des fonctions
    for i in range(1, len(p.children), 2):
        asm_f += f"{asm_function(p.children[i])}\n"
    
    prog_asm = prog_asm.replace("COMMANDE", asm_f)

    #Ecriture des strings
    for value, label in global_ctx.strings.items():
        value = value.encode('utf-8').decode('unicode_escape')
        decl_strings += f"{label}: db \"{value}\", 0\n"
    prog_asm = prog_asm.replace("DECL_STRINGS", decl_strings)

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
    
    if c.data == "declaration":
        type_var = c.children[0]
        var = c.children[1]
        if (len(c.children) > 2):
            exp = c.children[2]
            return f"{type_var} {var.value} = {pp_expression(exp)}"
        return f"{type_var} {var.value}"
    
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
    has_type = len(f.children) == 4

    type_offset = 1 if has_type else 0

    retour_type = f.children[0] if has_type else "void"
    name_fct = f.children[type_offset].value
    liste_vars_arg = f.children[type_offset + 1].children
    commande = f.children[type_offset + 2]

    liste_args = ""
    for arg in liste_vars_arg:
        type_arg = arg.children[0].value
        name_arg = arg.children[1].value
        liste_args += type_arg + " " + name_arg + ","
    return f"""{retour_type} {name_fct} ({liste_args[:-1]}){{
    {pp_commande(commande)}
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
            type_var = var.children[0].value
            name_var = var.children[1].value
            liste_vars += type_var + " " + name_var + ", " 
        output += f"{liste_vars[:-2]}\n{pp_function(fct)}\n"
    return output


if __name__ == "__main__":
    
    #Ouverture du programme d'un fichier externe
    with open("simple.c") as f:
        src = f.read()

    #Arbre syntaxique du programme
    ast = g.parse(src)
    #Affichage du code assembleur du programme
    print(asm_program(ast))
