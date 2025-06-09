class VariableContext:
    def __init__(self, name, var_type, offset=0, function_name=None):
        self.name = name
        self.var_type = var_type
        self.offset = offset
        self.function_name = function_name


class FunctionContext:
    def __init__(self, name, return_type):
        self.name = name
        self.args = {}
        self.locals = {}
        self.last_offset = 0
        self.return_type = return_type

    def add_arg(self, var_ctx):
        self.args[var_ctx.name] = var_ctx
        self.last_offset = var_ctx.offset

    def add_local(self, var_ctx):
        self.locals[var_ctx.name] = var_ctx


class GlobalContext:
    def __init__(self):
        self.functions = {}
        self.globals = {}
        self.strings = {}          # dictionnaire pour les chaînes littérales
        self.label_count = 0       # compteur pour les labels des chaînes
    
    def add_string_literal(self, value):
        if value in self.strings:
            return self.strings[value]
        label = f"str_{self.label_count}"
        self.strings[value] = label
        self.label_count += 1
        return label 

    def add_function(self, func_ctx):
        self.functions[func_ctx.name] = func_ctx

    def add_global(self, var_ctx):
        self.globals[var_ctx.name] = var_ctx

    def get_variable(self, var_name, current_func=None):
        if current_func:
            func_ctx = self.functions.get(current_func)
            if not func_ctx:
                raise NameError(f"Fonction non définie : '{current_func}'")

            if var_name in func_ctx.locals:
                return func_ctx.locals[var_name]
            if var_name in func_ctx.args:
                return func_ctx.args[var_name]

        if var_name in self.globals:
            return self.globals[var_name]

        raise NameError(f"Variable non définie : '{var_name}'")
    
    def has_function(self, fct_name):
        return fct_name in self.functions
    
    def get_function(self,fct_name):
        if not self.has_function(fct_name):
            raise NameError(f"Fonction non définie : '{fct_name}'")
        return self.functions.get(fct_name)

    def nb_args(self, fct_name):
        if not self.has_function(fct_name):
            raise NameError(f"Fonction non définie : '{fct_name}'")
        return len(self.functions[fct_name].args)