def calculate(expression_str):
    # VULNERABLE: eval() on user input allows arbitrary code execution
    result = eval(expression_str)
    return result

def process_command(cmd):
    # VULNERABLE: Using exec() on untrusted input
    exec(cmd)
    return "Command executed"

def dynamic_import(module_name):
    # VULNERABLE: __import__ with user-controlled input
    mod = __import__(module_name)
    return mod