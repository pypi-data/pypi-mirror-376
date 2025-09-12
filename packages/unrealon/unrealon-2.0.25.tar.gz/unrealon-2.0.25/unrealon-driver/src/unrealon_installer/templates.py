"""
Jinja2 template engine for batch files.
"""

from pathlib import Path
from typing import Dict, Any
import json
from jinja2 import Environment, FileSystemLoader


class TemplateEngine:
    """Jinja2-based template engine for Windows batch files."""
    
    def __init__(self):
        # Get batch templates directory
        templates_dir = Path(__file__).parent / "batch_templates"
        
        # Create Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def render_start_bat(self, parser_name: str, config: Dict[str, Any]) -> str:
        """Render START.bat file."""
        template = self.env.get_template('start.bat.j2')
        
        context = {
            'parser_name': parser_name,
            'config': config,
            'config_json': json.dumps(config, indent=None),
            'browsers_list': ', '.join(config.get('browsers_needed', ['chromium'])),
            'has_proxy': False,  # Removed proxy support detection
            'has_persistent': config.get('supports_persistent', True)  # Default to True
        }
        
        return template.render(**context)
    
    def render_quick_run_bat(self, parser_name: str, config: Dict[str, Any]) -> str:
        """Render QUICK_RUN.bat file."""
        template = self.env.get_template('quick_run.bat.j2')
        
        context = {
            'parser_name': parser_name,
            'config': config
        }
        
        return template.render(**context)
    
    def render_test_bat(self, parser_name: str, config: Dict[str, Any]) -> str:
        """Render TEST.bat file."""
        template = self.env.get_template('test.bat.j2')
        
        context = {
            'parser_name': parser_name,
            'config': config
        }
        
        return template.render(**context)
