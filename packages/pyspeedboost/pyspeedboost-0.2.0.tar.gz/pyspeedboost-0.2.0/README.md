# PySpeedBoost

PySpeedBoost is a Python library designed to significantly improve Python execution speed by automatically generating and using optimized binary counterparts of Python scripts using Nuitka.

## Features

- Automatic compilation of Python scripts to optimized binaries
- Seamless integration with existing code via decorators
- Intelligent caching system to avoid recompilation of unchanged scripts
- Command-line interface for easy use
- Cross-platform support (tested on Linux)

## Installation

### Prerequisites

- Python 3.7+
- C++ compiler (g++ or clang)
- patchelf (required on Linux systems)

### System Dependencies

On Ubuntu/Debian systems:
```bash
sudo apt-get update
sudo apt-get install python3-dev g++ patchelf
```

On CentOS/RHEL systems:
```bash
sudo yum install python3-devel gcc-c++ patchelf
```

### Install PySpeedBoost

```bash
pip install pyspeedboost
```

Or install from source:
```bash
git clone https://github.com/Chrispin-m/pyspeedboost.git
cd pyspeedboost
pip install -e .
```

## Usage

### Basic Usage with Decorator

```python
# app.py
from pyspeedboost import speedboost

@speedboost
def main():
    # Your computationally intensive code here
    result = 0
    for i in range(1000000):
        result += i
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
```

Run your script normally:
```bash
python app.py
```

On the first run, PySpeedBoost will compile your script to a binary. Subsequent runs will use the compiled binary for faster execution.

### Advanced Configuration

```python
from pyspeedboost import PySpeedBoost, CompilerConfig

# Create a custom configuration
config = CompilerConfig(
    output_dir="binaries",
    optimization_level=2,
    enable_lto=True,
    quiet_mode=False
)

# Create compiler instance
compiler = PySpeedBoost(config)

# Compile a specific script
compiler.compile("my_script.py")

# Force recompilation
compiler.compile("my_script.py", force=True)
```

### Command Line Interface

```bash
# Compile a script
pyspeedboost compile my_script.py

# Run a script with binary acceleration
pyspeedboost run my_script.py

# Clean compiled binaries
pyspeedboost clean

# Show version information
pyspeedboost version
```

## Performance

PySpeedBoost can significantly improve execution speed for CPU-intensive applications. However, the performance gain varies depending on the nature of your code:

- Best for computationally intensive applications
- Less beneficial for I/O-bound applications
- First run includes compilation time, so it may be slower

### Example Performance Results

```
Running with standard Python...
Running compiled version...
Interpreted time: 0.6244 seconds
Compiled time: 0.6573 seconds
Speedup: 0.95x
```

Note: In this specific test, the compiled version was slightly slower(first run on top), but performance gains are typically more significant for more complex computations.

## Testing

To verify your installation, run the test suite:

```bash
# Run unit tests
python -m pytest tests/test_pyspeedboost.py -v

# Run performance test
python tests/performance_test.py
```

Expected test output:
```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-8.4.2, pluggy-1.6.0 -- /dirs/pyspeedboost/venv/bin/python
cachedir: .pytest_cache
rootdir: /dirs/pyspeedboost
collected 4 items                                                              

tests/test_pyspeedboost.py::test_compiler_initialization PASSED          [ 25%]
tests/test_pyspeedboost.py::test_binary_path_generation PASSED           [ 50%]
tests/test_pyspeedboost.py::test_compile_and_run_simple_script PASSED    [ 75%]
tests/test_pyspeedboost.py::test_decorator_functionality PASSED          [100%]

============================== 4 passed in 0.73s ===============================
```

## Limitations

- May not work with all Python packages
- Dynamic code execution (eval, exec) may have limited optimization
- Cross-platform compatibility requires recompilation
- Initial compilation can be time-consuming for large projects

## Troubleshooting

### Common Issues

1. **Compilation fails**: Ensure you have all required system dependencies installed
2. **Binary not found**: Check that patchelf is installed on Linux systems
3. **Permission denied**: Make sure the binary has execute permissions

### Getting Help

If you encounter issues:
1. Check that all system dependencies are installed
2. Ensure you have the latest version of PySpeedBoost
3. Check the [Nuitka documentation](https://nuitka.net/) for compilation issues

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please file an issue on our GitHub repository.# pyspeedboost
