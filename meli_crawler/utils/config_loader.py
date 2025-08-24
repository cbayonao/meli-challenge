import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """
    Class to load and manage YAML configuration files
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration loader
        
        Args:
            config_dir: Configuration directory. If None, use the default directory
        """
        if config_dir is None:
            current_dir = Path(__file__).parent
            self.config_dir = current_dir.parent / 'config'
        else:
            self.config_dir = Path(config_dir)
            
        self._cache = {}  # Cache to avoid reloading files
    
    def load_yaml(self, filename: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Load a YAML file
        
        Args:
            filename: YAML file name (with or without extension)
            use_cache: If True, use cache to avoid reloading
            
        Returns:
            Dictionary with the file content
        """
        # Add .yaml extension if not present
        if not filename.endswith('.yaml') and not filename.endswith('.yml'):
            filename += '.yaml'
            
        # Check cache
        if use_cache and filename in self._cache:
            return self._cache[filename]
            
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
            
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                
            # Save in cache
            if use_cache:
                self._cache[filename] = config
                
            return config
            
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML {filename}: {e}")
        except Exception as e:
            raise Exception(f"Error loading configuration {filename}: {e}")
    
    def get_selectors_config(self) -> Dict[str, Any]:
        """Get selectors configuration"""
        return self.load_yaml('selectors.yaml')
    
    def reload_config(self, filename: Optional[str] = None):
        """
        Reload configuration (useful for development)
        
        Args:
            filename: Specific file to reload. If None, clear all cache
        """
        if filename:
            self._cache.pop(filename, None)
        else:
            self._cache.clear()
    
    def list_config_files(self) -> list:
        """List all available configuration files"""
        if not self.config_dir.exists():
            return []
            
        return [f.name for f in self.config_dir.iterdir() 
                if f.suffix in ['.yaml', '.yml']]


# Global instance for spiders
config_loader = ConfigLoader()