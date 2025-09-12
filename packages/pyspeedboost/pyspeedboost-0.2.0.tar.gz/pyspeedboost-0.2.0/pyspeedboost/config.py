import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class CompilerConfig:
    """Configuration for the PySpeedBoost compiler"""
    output_dir: str = "__pyspeedboost_bin__"
    keep_temp_files: bool = False
    optimization_level: int = 1  # Reduced from 2 to 1 for better compatibility
    enable_lto: bool = False  # Disabled by default for better compatibility
    enable_ccache: bool = True  # Use ccache if available
    quiet_mode: bool = False  # Suppress compilation output
    
    def __post_init__(self):
        """Validate configuration"""
        if not 0 <= self.optimization_level <= 3:
            raise ValueError("optimization_level must be between 0 and 3")
            
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)