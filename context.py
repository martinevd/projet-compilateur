class VariableContext:
    def __init__(self, name, var_type, offset=None, function_name=None):
        self.name = name
        self.var_type = var_type
        self.offset = offset
        self.function_name = function_name


class FunctionContext:
    def __init__(self, name):
        self.name = name
        self.args = {}
        self.locals = {}

    def add_arg(self, var_ctx):
        self.args[var_ctx.name] = var_ctx

    def add_local(self, var_ctx):
        self.locals[var_ctx.name] = var_ctx


class GlobalContext:
    def __init__(self):
        self.functions = {}
        self.globals = {}

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

    def nb_args(self, fct_name):
        if fct_name not in self.functions:
            raise NameError(f"Fonction non définie : '{fct_name}'")
        return len(self.functions[fct_name].args)

    def set_offset_arg(self, var_name, current_func, offset):
        func_ctx = self.functions.get(current_func)
        if not func_ctx:
            raise NameError(f"Fonction non définie : '{current_func}'")

        if var_name in func_ctx.args:
            func_ctx.args[var_name].offset = offset
        else:
            raise NameError(f"Argument non défini : '{var_name}'")

    def set_offset_local(self, var_name, current_func, offset):
        func_ctx = self.functions.get(current_func)
        if not func_ctx:
            raise NameError(f"Fonction non définie : '{current_func}'")

        if var_name in func_ctx.locals:
            func_ctx.locals[var_name].offset = offset
        else:
            raise NameError(f"Variable locale non définie : '{var_name}'")
