#!/usr/bin/env python3
"""
Example script demonstrating SQL generation from a configuration file.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the sql_generator package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sql_generator import SQLConfig, SQLGenerator


def main():
    """Main function demonstrating SQL generation from a configuration file."""

    # Get the templates directory and config file path
    templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    config_file = os.path.join(os.path.dirname(__file__), "query_config.json")

    # Load the configuration from the JSON file
    config = SQLConfig.from_json_file(config_file)

    # Initialize the generator
    generator = SQLGenerator(templates_dir, dialect="postgresql")

    # Generate SQL from the configuration
    sql = generator.generate_from_config(config.to_dict())

    print("Generated SQL (PostgreSQL):")
    print(sql)
    print()

    # Generate the same SQL for MySQL
    generator.set_dialect("mysql")
    sql = generator.generate_from_config(config.to_dict())

    print("Generated SQL (MySQL):")
    print(sql)
    print()

    # Modify the configuration programmatically
    config.set("limit", 50)
    config.set("offset", 100)

    # Generate SQL with the modified configuration
    generator.set_dialect("postgresql")
    sql = generator.generate_from_config(config.to_dict())

    print("Generated SQL with modified configuration:")
    print(sql)


if __name__ == "__main__":
    main()
