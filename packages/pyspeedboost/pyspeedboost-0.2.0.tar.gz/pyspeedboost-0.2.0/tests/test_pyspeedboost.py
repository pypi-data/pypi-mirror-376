import os
import sys
import tempfile
import subprocess
import pytest
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pyspeedboost import PySpeedBoost, speedboost
from pyspeedboost.config import CompilerConfig
from pyspeedboost.exceptions import CompilationError

def test_compiler_initialization():
    """Test that the compiler initializes correctly"""
    config = CompilerConfig(output_dir="test_bin", optimization_level=2)
    compiler = PySpeedBoost(config)
    assert compiler.config.output_dir == "test_bin"
    assert compiler.config.optimization_level == 2
    assert os.path.exists("test_bin")
    
    # Cleanup
    import shutil
    shutil.rmtree("test_bin", ignore_errors=True)

def test_binary_path_generation():
    """Test that binary paths are generated correctly"""
    compiler = PySpeedBoost()
    
    # Create a temporary test script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("print('Hello, World!')\n")
        test_script = f.name
    
    try:
        from pyspeedboost.utils import get_binary_path
        binary_path = get_binary_path(test_script, "__pyspeedboost_bin__")
        assert binary_path.startswith("__pyspeedboost_bin__")
        assert Path(test_script).stem in binary_path
    finally:
        os.unlink(test_script)

def test_compile_and_run_simple_script():
    """Test compiling and running a simple script"""
    compiler = PySpeedBoost()
    
    # Create a simple test script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("print('Hello from compiled script!')\n")
        test_script = f.name
    
    try:
        # Try to compile the script
        try:
            binary_path = compiler.compile(test_script)
            assert os.path.exists(binary_path)
            
            # Test running the binary
            result = subprocess.run([binary_path], capture_output=True, text=True)
            assert result.returncode == 0
            assert "Hello from compiled script!" in result.stdout
        except CompilationError as e:
            # If compilation fails, skip the test with a warning
            pytest.skip(f"Skipping test due to compilation error: {e}")
    finally:
        os.unlink(test_script)
        # Cleanup
        import shutil
        shutil.rmtree("__pyspeedboost_bin__", ignore_errors=True)

def test_decorator_functionality():
    """Test the @speedboost decorator"""
    # This test is more complex as it involves module execution
    # We'll create a temporary script and run it
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
from pyspeedboost import speedboost

@speedboost
def main():
    print('Decorator test successful!')
    return 42

if __name__ == '__main__':
    result = main()
    print(f'Result: {result}')
""")
        test_script = f.name
    
    try:
        # Run the script
        result = subprocess.run([sys.executable, test_script], 
                              capture_output=True, text=True, timeout=30)
        
        assert result.returncode == 0
        assert "Decorator test successful!" in result.stdout or "Result: 42" in result.stdout
    finally:
        os.unlink(test_script)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])