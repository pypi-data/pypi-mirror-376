import os
import sys
import hashlib
import tempfile
import shutil
import inspect
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pyspeedboost")

def get_script_hash(script_path: str) -> str:
    """Generate a hash of the script content for caching"""
    with open(script_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def get_binary_path(script_path: str, output_dir: str) -> str:
    """Generate the path for the compiled binary"""
    script_name = Path(script_path).stem
    script_hash = get_script_hash(script_path)
    
    if os.name == 'nt':  # Windows
        binary_name = f"{script_name}_{script_hash}.exe"
    else:  # Unix-like
        binary_name = f"{script_name}_{script_hash}"
    
    return os.path.join(output_dir, binary_name)

def is_binary_up_to_date(script_path: str, binary_path: str) -> bool:
    """Check if the binary is up to date with the script"""
    if not os.path.exists(binary_path):
        return False
    
    # Check if script has been modified since compilation
    script_mtime = os.path.getmtime(script_path)
    binary_mtime = os.path.getmtime(binary_path)
    
    return binary_mtime >= script_mtime

def get_main_script_path() -> Optional[str]:
    """Get the path of the main executing script"""
    try:
        # First try to get the main module's file path
        main_module = sys.modules['__main__']
        if hasattr(main_module, '__file__') and main_module.__file__:
            return os.path.abspath(main_module.__file__)
        
        # Fallback for interactive mode or other edge cases
        frame = inspect.stack()[-1]
        return os.path.abspath(frame.filename)
    except (AttributeError, IndexError):
        return None

def setup_logging(quiet: bool = False):
    """Configure logging for the library"""
    level = logging.WARNING if quiet else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )