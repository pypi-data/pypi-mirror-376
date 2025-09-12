"""
PySpeedBoost - Accelerate Python execution through binary compilation
"""

from .compiler import PySpeedBoost, speedboost
from .config import CompilerConfig
from .exceptions import CompilationError, BinaryExecutionError

__version__ = "0.2.0"
__all__ = ['PySpeedBoost', 'speedboost', 'CompilerConfig', 'CompilationError', 'BinaryExecutionError']