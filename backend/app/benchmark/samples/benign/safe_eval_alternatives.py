def calculate(expression_str):
    # SAFE: Using ast.literal_eval which only evaluates literals
    import ast
    try:
        result = ast.literal_eval(expression_str)
        return result
    except (ValueError, SyntaxError):
        raise ValueError("Invalid expression")

def process_command(cmd):
    # SAFE: Using a whitelist of allowed commands instead of exec()
    ALLOWED_COMMANDS = {"list", "status", "help"}
    if cmd not in ALLOWED_COMMANDS:
        raise ValueError(f"Command not allowed: {cmd}")
    # Dispatch to safe handler functions
    handlers = {"list": _handle_list, "status": _handle_status, "help": _handle_help}
    return handlers[cmd]()

def dynamic_import(module_name):
    # SAFE: Using a whitelist of allowed modules
    ALLOWED_MODULES = {"math", "json", "collections", "itertools"}
    if module_name not in ALLOWED_MODULES:
        raise ValueError(f"Module not allowed: {module_name}")
    import importlib
    mod = importlib.import_module(module_name)
    return mod

def _handle_list(): return "list"
def _handle_status(): return "ok"
def _handle_help(): return "help"