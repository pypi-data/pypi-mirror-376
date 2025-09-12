class PySpeedBoostError(Exception):
    """Base exception for PySpeedBoost errors"""
    pass

class CompilationError(PySpeedBoostError):
    """Exception raised when compilation fails"""
    pass

class BinaryExecutionError(PySpeedBoostError):
    """Exception raised when binary execution fails"""
    pass

class ConfigurationError(PySpeedBoostError):
    """Exception raised for configuration errors"""
    pass