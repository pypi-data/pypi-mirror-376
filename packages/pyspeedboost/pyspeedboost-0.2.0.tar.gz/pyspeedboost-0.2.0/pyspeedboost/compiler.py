import os
import sys
import subprocess
import tempfile
import shutil
import time
import logging
from typing import Optional, List, Dict, Any
from functools import wraps
from pathlib import Path

from .config import CompilerConfig
from .exceptions import CompilationError, BinaryExecutionError
from .utils import get_binary_path, is_binary_up_to_date, get_script_hash, setup_logging

logger = logging.getLogger("pyspeedboost")

class PySpeedBoost:
    """Main compiler class for PySpeedBoost"""
    
    def __init__(self, config: Optional[CompilerConfig] = None):
        self.config = config or CompilerConfig()
        setup_logging(self.config.quiet_mode)
        
    def _build_nuitka_command(self, script_path: str, binary_path: str) -> List[str]:
        """Build the Nuitka compilation command"""
        cmd = [
            sys.executable, "-m", "nuitka",
            "--standalone",
            "--remove-output",
            f"--output-dir={self.config.output_dir}",
            f"--output-filename={Path(binary_path).name}",
        ]
        
        # Only use basic optimization options that work across all Nuitka versions
        if self.config.optimization_level >= 1:
            cmd.append("--follow-imports")
        
        # Add quiet mode if enabled
        if self.config.quiet_mode:
            cmd.append("--quiet")
        
        cmd.append(script_path)
        return cmd
    
    def _check_nuitka_available(self) -> bool:
        """Check if Nuitka is available and working"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "nuitka", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def compile(self, script_path: str, force: bool = False) -> str:
        """Compile a Python script to binary"""
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script not found: {script_path}")
        
        # Check if Nuitka is available
        if not self._check_nuitka_available():
            raise CompilationError(
                "Nuitka is not available. Please install it with 'pip install nuitka' "
                "and ensure you have a C++ compiler installed."
            )
        
        binary_path = get_binary_path(script_path, self.config.output_dir)
        
        # Check if we need to recompile
        if not force and is_binary_up_to_date(script_path, binary_path):
            logger.info(f"Using cached binary: {binary_path}")
            return binary_path
        
        # Build and execute compilation command
        cmd = self._build_nuitka_command(script_path, binary_path)
        
        logger.info(f"Compiling {script_path} to binary...")
        start_time = time.time()
        
        try:
            # Capture output to provide better error messages
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if process.returncode != 0:
                error_msg = f"Compilation failed with return code {process.returncode}"
                if process.stderr:
                    error_msg += f"\nError output:\n{process.stderr}"
                if process.stdout:
                    error_msg += f"\nOutput:\n{process.stdout}"
                
                raise CompilationError(error_msg)
            
            compilation_time = time.time() - start_time
            logger.info(f"Compilation completed in {compilation_time:.2f} seconds")
            
            # Nuitka creates a .dist directory with the binary inside
            # The binary name is the same as the script name without extension
            script_name = os.path.splitext(os.path.basename(script_path))[0]
            dist_dir = os.path.join(self.config.output_dir, f"{script_name}.dist")
            
            if not os.path.exists(dist_dir):
                raise CompilationError(f"Expected distribution directory not found: {dist_dir}")
            
            # Find the binary in the dist directory
            binary_name = script_name
            if os.name == 'nt':  # Windows
                binary_name += '.exe'
            
            actual_binary_path = os.path.join(dist_dir, binary_name)
            
            if not os.path.exists(actual_binary_path):
                # Try to find any executable file in the dist directory
                for file in os.listdir(dist_dir):
                    if (os.name == 'nt' and file.endswith('.exe')) or (os.name != 'nt' and not file.endswith('.so')):
                        potential_binary = os.path.join(dist_dir, file)
                        if os.path.isfile(potential_binary) and os.access(potential_binary, os.X_OK):
                            actual_binary_path = potential_binary
                            break
                
                if not os.path.exists(actual_binary_path):
                    raise CompilationError(f"Could not find compiled binary in {dist_dir}")
            
            # Move the binary to the expected location
            shutil.move(actual_binary_path, binary_path)
            
            # Remove the dist directory
            shutil.rmtree(dist_dir)
            
            # Make sure the binary is executable
            os.chmod(binary_path, 0o755)
            
            return binary_path
            
        except subprocess.TimeoutExpired:
            raise CompilationError("Compilation timed out after 5 minutes")
        except subprocess.SubprocessError as e:
            raise CompilationError(f"Compilation process error: {e}")
    
    def run(self, script_path: str, *args, **kwargs) -> None:
        """Run a script using its compiled version if available"""
        try:
            binary_path = get_binary_path(script_path, self.config.output_dir)
            
            if is_binary_up_to_date(script_path, binary_path):
                # Run the compiled binary
                cmd = [binary_path] + list(args)
                
                # Replace current process with the binary
                os.execve(cmd[0], cmd, os.environ)
            else:
                # Fallback to Python interpretation
                self._run_interpreted(script_path, *args, **kwargs)
                
        except (CompilationError, BinaryExecutionError) as e:
            logger.warning(f"Failed to run compiled binary: {e}")
            logger.info("Falling back to interpreted execution")
            self._run_interpreted(script_path, *args, **kwargs)
    
    def _run_interpreted(self, script_path: str, *args, **kwargs) -> None:
        """Run the script using the Python interpreter"""
        try:
            # Add script directory to path
            script_dir = os.path.dirname(os.path.abspath(script_path))
            if script_dir not in sys.path:
                sys.path.insert(0, script_dir)
            
            # Execute the script
            with open(script_path, 'r') as f:
                code = compile(f.read(), script_path, 'exec')
            
            # Prepare globals with arguments
            globals_dict = {
                '__name__': '__main__',
                '__file__': script_path,
                'args': args,
                'kwargs': kwargs
            }
            
            exec(code, globals_dict)
            
        except Exception as e:
            raise BinaryExecutionError(f"Failed to execute script: {e}")

def speedboost(func):
    """Decorator to compile and run the main function as a binary"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        from .utils import get_main_script_path
        
        script_path = get_main_script_path()
        if script_path:
            compiler = PySpeedBoost()
            try:
                # Try to compile and run as binary
                compiler.run(script_path, *args, **kwargs)
            except Exception as e:
                logger.warning(f"Binary execution failed: {e}")
                logger.info("Falling back to standard execution")
                return func(*args, **kwargs)
        else:
            # Fallback to standard execution
            return func(*args, **kwargs)
    
    return wrapper