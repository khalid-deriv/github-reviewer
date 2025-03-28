import yaml
import os
from core.logger import setup_logger

class ConfigValidationError(Exception):
    """Custom exception for configuration validation errors."""
    pass

# Initialize logger
logger = setup_logger()

def load_config(file_path):
    """Load the YAML configuration file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    logger.info(f"Loading configuration file: {file_path}")
    
    with open(file_path, 'r') as file:
        try:
            config = yaml.safe_load(file)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file: {e}")
            raise ConfigValidationError(f"Error parsing YAML file: {e}")
    
    logger.info("Configuration file loaded successfully.")
    return config

def validate_config(config):
    """Validate the structure and required fields of the configuration."""
    required_fields = ["directives", "exclusions", "llm_parameters", "llm_backends", "update_frequency"]
    
    logger.info("Validating configuration structure and required fields.")
    
    for field in required_fields:
        if field not in config:
            logger.error(f"Missing required field: {field}")
            raise ConfigValidationError(f"Missing required field: {field}")
    
    if not isinstance(config["directives"], list):
        raise ConfigValidationError("`directives` must be a list of strings.")
    
    if not isinstance(config["exclusions"], list):
        raise ConfigValidationError("`exclusions` must be a list of strings.")
    
    llm_params = config.get("llm_parameters", {})
    if not isinstance(llm_params, dict):
        raise ConfigValidationError("`llm_parameters` must be a dictionary.")
    
    for param in ["temperature", "max_tokens", "model_name"]:
        if param not in llm_params:
            raise ConfigValidationError(f"Missing required LLM parameter: {param}")
    
    if not isinstance(config["llm_backends"], list):
        raise ConfigValidationError("`llm_backends` must be a list of dictionaries.")
    
    for backend in config["llm_backends"]:
        if not isinstance(backend, dict) or "backend_name" not in backend or "token" not in backend:
            raise ConfigValidationError("Each LLM backend must be a dictionary with `backend_name` and `token`.")
    
    if not isinstance(config["update_frequency"], str):
        raise ConfigValidationError("`update_frequency` must be a string.")
    
    logger.info("Configuration validation completed successfully.")

def main():
    """Main function to load and validate the configuration."""
    config_path = "../config/schema.yaml"  # Adjust path as needed
    try:
        config = load_config(config_path)
        validate_config(config)
        print("Configuration is valid.")
    except (FileNotFoundError, ConfigValidationError) as e:
        print(f"Configuration validation failed: {e}")

if __name__ == "__main__":
    main()
