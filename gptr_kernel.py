#!/usr/bin/env python3
"""
Microkernel CLI for GPT Researcher
Minimal core that dispatches to plugins via uvx
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

class GPTRKernel:
    """Minimal kernel that dispatches commands to plugins via uvx"""
    
    def __init__(self):
        self.config = self._load_config()
        self.plugins = self._discover_plugins()
    
    def _load_config(self) -> Dict[str, str]:
        """Load configuration from environment variables"""
        return {
            'llm_provider': os.getenv('GPTR_LLM_PROVIDER', 'gpt5'),
            'llm_model': os.getenv('GPTR_LLM_MODEL', 'gpt-5'),
            'data_source': os.getenv('GPTR_DATA_SOURCE', 'web'),
            'exporter': os.getenv('GPTR_EXPORTER', 'markdown'),
            'output_dir': os.getenv('GPTR_OUTPUT_DIR', './outputs'),
            'cache_dir': os.getenv('GPTR_CACHE_DIR', str(Path.home() / '.gptr' / 'cache')),
            'plugin_registry': os.getenv('GPTR_PLUGIN_REGISTRY', str(Path.home() / '.gptr' / 'plugins.json')),
            'log_level': os.getenv('GPTR_LOG_LEVEL', 'INFO'),
            'dry_run': os.getenv('GPTR_DRY_RUN', 'false').lower() == 'true',
        }
    
    def _discover_plugins(self) -> Dict[str, str]:
        """Discover available plugins from registry or defaults"""
        # For now, use local scripts - later these will be pip packages
        script_dir = Path(__file__).parent
        return {
            'research': str(script_dir / 'gptr_research_plugin.py'),
            'export': str(script_dir / 'gptr_export_plugin.py'),
            'config': str(script_dir / 'gptr_config_plugin.py'),
        }
    
    def dispatch(self, command: str, args: Dict[str, Any]) -> int:
        """Dispatch command to appropriate plugin via uvx or directly"""
        
        # Get plugin for command
        plugin = self.plugins.get(command)
        if not plugin:
            print(f"Error: Unknown command '{command}'", file=sys.stderr)
            return 1
        
        # Prepare plugin input
        plugin_input = {
            'command': command,
            'args': args,
            'config': self.config,
        }
        
        # Run plugin - if it's a local file, run directly with python
        # Later, we'll use uvx for published packages
        try:
            if plugin.endswith('.py') and Path(plugin).exists():
                # Local script - run directly
                result = subprocess.run(
                    [sys.executable, plugin],
                    input=json.dumps(plugin_input),
                    text=True,
                    capture_output=True,
                    env={**os.environ, **self._config_to_env()}
                )
            else:
                # Package - run via uvx
                result = subprocess.run(
                    ['uvx', plugin],
                    input=json.dumps(plugin_input),
                    text=True,
                    capture_output=True,
                    env={**os.environ, **self._config_to_env()}
                )
            
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            
            return result.returncode
            
        except Exception as e:
            print(f"Error running plugin '{plugin}': {e}", file=sys.stderr)
            return 1
    
    
    def _config_to_env(self) -> Dict[str, str]:
        """Convert config to environment variables"""
        return {
            f'GPTR_{k.upper()}': str(v) 
            for k, v in self.config.items()
        }
    
    def run(self, argv: Optional[list] = None) -> int:
        """Main entry point"""
        import argparse
        
        parser = argparse.ArgumentParser(
            prog='gptr',
            description='GPT Researcher - Microkernel CLI'
        )
        
        subparsers = parser.add_subparsers(dest='command', required=True)
        
        # Research command (wraps existing functionality)
        research_parser = subparsers.add_parser('research', help='Conduct research')
        research_parser.add_argument('query', help='Research query')
        research_parser.add_argument('--report-type', choices=[
            'research_report', 'detailed_report', 'resource_report',
            'outline_report', 'custom_report', 'subtopic_report'
        ], default='research_report')
        research_parser.add_argument('--tone', default='objective')
        research_parser.add_argument('--domains', nargs='*', default=[])
        research_parser.add_argument('--dry-run', action='store_true', 
                                    help='Simulate research without making API calls')
        
        # Config command (placeholder)
        config_parser = subparsers.add_parser('config', help='Manage configuration')
        config_parser.add_argument('action', choices=['show', 'set', 'get'])
        config_parser.add_argument('key', nargs='?')
        config_parser.add_argument('value', nargs='?')
        
        # Parse arguments
        args = parser.parse_args(argv)
        
        # Convert args to dict for dispatch
        args_dict = vars(args)
        command = args_dict.pop('command')
        
        # Dispatch to plugin
        return self.dispatch(command, args_dict)


def main():
    """CLI entry point"""
    kernel = GPTRKernel()
    sys.exit(kernel.run())


if __name__ == '__main__':
    main()