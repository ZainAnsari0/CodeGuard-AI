import pickle
import yaml
import json

def load_user_data(data):
    # SAFE: Using json.loads for deserialization of untrusted data
    return json.loads(data)

def load_config(config_str):
    # SAFE: Using yaml.safe_load which only parses basic YAML tags
    return yaml.safe_load(config_str)

def restore_state(serialized):
    # SAFE: Using ast.literal_eval instead of eval for safe evaluation
    import ast
    return ast.literal_eval(serialized)