import os
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader, Template


class TemplateLoader:
    """
    Utility class for loading and managing SQL templates.
    """

    def __init__(self, templates_dir: str):
        """
        Initialize the template loader.

        Args:
            templates_dir: Directory containing SQL template files
        """
        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(templates_dir), trim_blocks=True, lstrip_blocks=True
        )
        self.templates_cache: Dict[str, Template] = {}

    def get_template(self, template_name: str) -> Template:
        """
        Get a template by name.

        Args:
            template_name: Name of the template file

        Returns:
            Jinja2 Template object
        """
        if template_name not in self.templates_cache:
            self.templates_cache[template_name] = self.env.get_template(template_name)
        return self.templates_cache[template_name]

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a template with the given context.

        Args:
            template_name: Name of the template file
            context: Dictionary with variables to be used in the template

        Returns:
            Rendered SQL statement
        """
        template = self.get_template(template_name)
        return template.render(**context)

    def list_templates(self) -> list:
        """
        List all available templates.

        Returns:
            List of template names
        """
        return self.env.list_templates()

    def add_filter(self, name: str, filter_func: callable) -> None:
        """
        Add a custom filter to the Jinja2 environment.

        Args:
            name: Name of the filter
            filter_func: Filter function
        """
        self.env.filters[name] = filter_func

    def add_global(self, name: str, value: Any) -> None:
        """
        Add a global variable to the Jinja2 environment.

        Args:
            name: Name of the global variable
            value: Value of the global variable
        """
        self.env.globals[name] = value
