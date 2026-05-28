import pickle
import yaml

def load_user_data(data):
    # VULNERABLE: Deserializing untrusted data with pickle
    return pickle.loads(data)

def load_config(config_str):
    # VULNERABLE: yaml.load without SafeLoader allows arbitrary code execution
    return yaml.load(config_str, Loader=yaml.Loader)

def restore_state(serialized):
    # VULNERABLE: Using eval on untrusted input
    return eval(serialized)