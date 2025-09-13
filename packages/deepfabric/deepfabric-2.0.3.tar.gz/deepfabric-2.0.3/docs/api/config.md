# Configuration API

The DeepFabricConfig class provides programmatic access to YAML configuration loading, validation, and parameter management. This API enables dynamic configuration manipulation, parameter override, and integration with external configuration systems.

## DeepFabricConfig Class

The configuration system loads YAML files and provides structured access to all generation parameters:

```python
from deepfabric import DeepFabricConfig

# Load configuration from YAML
config = DeepFabricConfig.from_yaml("config.yaml")

# Access configuration sections
tree_args = config.get_tree_args()
generator_args = config.get_engine_args()
dataset_config = config.get_dataset_config()
```

### Loading Configurations

#### from_yaml(filepath: str)

Class method for loading configurations from YAML files:

```python
config = DeepFabricConfig.from_yaml("production_config.yaml")
```

Supports full YAML syntax including comments, multi-line strings, and complex nested structures.

#### from_dict(config_dict: Dict)

Create configuration from Python dictionaries:

```python
config_data = {
    "system_prompt": "Custom system prompt",
    "topic_tree": {
        "args": {
            "root_prompt": "Programming concepts",
            "tree_degree": 4,
            "tree_depth": 2
        }
    }
}

config = DeepFabricConfig.from_dict(config_data)
```

Enables programmatic configuration construction and dynamic modification.

### Configuration Access

#### get_tree_args(**overrides)

Extract TreeArguments with optional parameter overrides:

```python
# Basic usage
tree_args = config.get_tree_args()

# With overrides
tree_args = config.get_tree_args(
    tree_degree=5,
    temperature=0.9,
    provider="anthropic",
    model="claude-3-opus"
)
```

Overrides merge with base configuration, enabling parameter experimentation without modifying files.

#### get_topic_graph_args(**overrides)

Extract GraphArguments for graph-based topic modeling:

```python
graph_args = config.get_topic_graph_args(
    graph_degree=4,
    graph_depth=3,
    temperature=0.8
)
```

Returns appropriate arguments for Graph class instantiation.

#### get_engine_args(**overrides)

Extract DataSetGeneratorArguments with override support:

```python
generator_args = config.get_engine_args(
    temperature=0.7,
    provider="openai",
    model="gpt-4",
    max_retries=5
)
```

Enables dynamic adjustment of generation parameters.

#### get_dataset_config()

Access dataset creation and output configuration:

```python
dataset_config = config.get_dataset_config()

# Access specific sections
creation_params = dataset_config["creation"]
output_path = dataset_config["save_as"]
```

Returns dictionary with dataset-specific configuration including execution parameters and file paths.

#### get_huggingface_config()

Extract Hugging Face Hub integration settings:

```python
hf_config = config.get_huggingface_config()

repository = hf_config.get("repository")
token = hf_config.get("token")
tags = hf_config.get("tags", [])
```

Returns empty dictionary if Hugging Face integration is not configured.

### Placeholder System

The configuration system supports placeholder substitution for parameter reuse:

#### System Prompt Placeholders

The `<system_prompt_placeholder>` enables reuse of global system prompts:

```python
# Configuration with placeholder
config_data = {
    "system_prompt": "You are an educational content creator.",
    "topic_tree": {
        "args": {
            "model_system_prompt": "<system_prompt_placeholder>"
        }
    },
    "data_engine": {
        "args": {
            "system_prompt": "<system_prompt_placeholder>"
        }
    }
}

config = DeepFabricConfig.from_dict(config_data)

# Placeholders are resolved automatically
tree_args = config.get_tree_args()
assert tree_args.model_system_prompt == "You are an educational content creator."
```

#### Custom Placeholders

Extend the placeholder system for custom variables:

```python
config.add_placeholder("model_name_placeholder", "openai/gpt-4")
config.add_placeholder("temperature_placeholder", 0.8)

# Use in configuration
config_with_placeholders = {
    "topic_tree": {
        "args": {
            "model_name": "<model_name_placeholder>",
            "temperature": "<temperature_placeholder>"
        }
    }
}
```

### Configuration Validation

#### validate()

Comprehensive configuration validation:

```python
validation_result = config.validate()

if validation_result.is_valid:
    print("Configuration is valid")
else:
    for error in validation_result.errors:
        print(f"Error: {error}")
    for warning in validation_result.warnings:
        print(f"Warning: {warning}")
```

Returns ValidationResult object with detailed feedback about configuration issues.

#### check_required_fields()

Verify presence of essential configuration sections:

```python
missing_fields = config.check_required_fields()
if missing_fields:
    print(f"Missing required fields: {missing_fields}")
```

#### validate_parameters()

Check parameter values for common issues:

```python
parameter_issues = config.validate_parameters()
for issue in parameter_issues:
    print(f"Parameter issue: {issue.field} - {issue.message}")
```

### Provider Integration

#### construct_model_string(provider: str, model: str)

Utility function for creating LiteLLM-compatible model strings:

```python
from deepfabric.config import construct_model_string

model_string = construct_model_string("openai", "gpt-4")
# Returns: "openai/gpt-4"

model_string = construct_model_string("anthropic", "claude-3-opus")
# Returns: "anthropic/claude-3-opus"
```

#### get_provider_config(provider: str)

Extract provider-specific configuration:

```python
openai_config = config.get_provider_config("openai")
anthropic_config = config.get_provider_config("anthropic")
```

Returns provider-specific settings including authentication requirements and default parameters.

### Advanced Usage

#### Configuration Merging

Merge multiple configurations for complex scenarios:

```python
base_config = DeepFabricConfig.from_yaml("base_config.yaml")
override_config = DeepFabricConfig.from_yaml("experiment_overrides.yaml")

merged_config = base_config.merge(override_config)
```

#### Environment Variable Integration

Inject environment variables into configuration:

```python
config = DeepFabricConfig.from_yaml("config.yaml")
config.inject_environment_variables()

# Automatically populates API keys and other environment-based settings
```

#### Dynamic Parameter Updates

Modify configuration parameters at runtime:

```python
config.update_parameter("topic_tree.args.tree_degree", 5)
config.update_parameter("data_engine.args.temperature", 0.9)

# Updated parameters reflected in subsequent argument extraction
updated_args = config.get_tree_args()
```

### Error Handling

Configuration-specific error handling:

```python
from deepfabric import ConfigurationError, ValidationError

try:
    config = DeepFabricConfig.from_yaml("config.yaml")
    tree_args = config.get_tree_args()
except ConfigurationError as e:
    print(f"Configuration loading failed: {e}")
except ValidationError as e:
    print(f"Configuration validation failed: {e}")
```

### Integration Examples

Common patterns for configuration integration:

```python
# CLI-style parameter overrides
def create_generator_with_overrides(config_path, **overrides):
    config = DeepFabricConfig.from_yaml(config_path)
    generator_args = config.get_engine_args(**overrides)
    return DataSetGenerator(args=generator_args)

generator = create_generator_with_overrides(
    "base_config.yaml",
    temperature=0.8,
    provider="anthropic",
    model="claude-3-opus"
)

# Multi-environment configuration
def load_environment_config(environment):
    base_config = DeepFabricConfig.from_yaml("base_config.yaml")
    env_overrides = DeepFabricConfig.from_yaml(f"{environment}_overrides.yaml")
    return base_config.merge(env_overrides)

prod_config = load_environment_config("production")
dev_config = load_environment_config("development")
```