import yaml
import os
from pydantic import ValidationError

from browser_env.models import Config

from dotenv import load_dotenv

loaded_envvars = load_dotenv(override=True)
assert loaded_envvars, "Have not loaded the environment variables"

def replace_env_variables(data):
    """Recursively replace placeholders with environment variables in the given data."""
    if isinstance(data, dict):
        return {k: replace_env_variables(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [replace_env_variables(v) for v in data]
    elif isinstance(data, str):
        return os.path.expandvars(data)
    return data

# Load and process the YAML file
with open('init_browser_conf.yaml', 'r') as file:
    raw_config_data = yaml.safe_load(file)
    config_data = replace_env_variables(raw_config_data)

# Parse the processed data into the Config model
try:
    config: Config = Config(**config_data)
except ValidationError as e:
    print(e)
    print("Please adjust your models restrictions in model.py or update your configuration")
"""
config as a pydantic Config object for automatic configuration validation:
e.g.
    browse_config
        > params
            >sites
                >SHOPPING
                    >token 
    you may access with `browse_config.params.sites.SHOPPING.token`
"""

if __name__=="__main__":
    print(config)
    print(config.params.sites.keys())