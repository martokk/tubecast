"""
This type stub file was generated by pyright.
"""

from .base import BaseTemplate

class JinjaTemplate(BaseTemplate):
    """
    This template is mostly for demo purposes.
    You probably want to subclass from it
    and make more clear environment initialization.
    """
    DEFAULT_JINJA_ENVIRONMENT = ...
    def __init__(self, template_text, environment=...) -> None:
        ...

    def compile_template(self):
        ...

    def render(self, **kwargs):
        ...
