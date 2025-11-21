#!/usr/bin/env python3
"""
Example script demonstrating SQL generation from a YAML configuration file.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the sql_generator package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sql_generator import SQLConfig, SQLGenerator


def main():
    """Main function demonstrating SQL generation from a YAML configuration file."""

    # Get the templates directory and config file path
    templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    config_file = os.path.join(os.path.dirname(__file__), "query_config.yaml")

    # Load the configuration from the YAML file
    config = SQLConfig.from_yaml_file(config_file)

    # Initialize the generator
    generator = SQLGenerator(templates_dir, dialect="postgresql")

    # Generate SQL from the configuration
    sql = generator.generate_from_config(config.to_dict())

    print("Generated SQL from YAML configuration (PostgreSQL):")
    print(sql)
    print()

    # Convert the YAML configuration to JSON
    json_output = config.to_json()
    print("Configuration as JSON:")
    print(json_output)


if __name__ == "__main__":
    main()
