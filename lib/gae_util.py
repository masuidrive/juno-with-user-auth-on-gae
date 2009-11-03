import os

def is_development_env():
    return os.environ['SERVER_SOFTWARE'].startswith('Development/')
