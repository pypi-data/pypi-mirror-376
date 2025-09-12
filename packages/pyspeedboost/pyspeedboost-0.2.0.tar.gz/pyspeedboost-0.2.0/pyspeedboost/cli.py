import argparse
import sys
import os
from pathlib import Path

from .compiler import PySpeedBoost
from .config import CompilerConfig
from .exceptions import CompilationError, BinaryExecutionError
from .utils import setup_logging

def main():
    """Command-line interface for PySpeedBoost"""
    parser = argparse.ArgumentParser(
        description="PySpeedBoost: Accelerate Python execution with binary compilation"
    )
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Compile command
    compile_parser = subparsers.add_parser('compile', help='Compile a Python script to binary')
    compile_parser.add_argument('script', help='Python script to compile')
    compile_parser.add_argument('-f', '--force', action='store_true', 
                               help='Force recompilation even if binary exists')
    compile_parser.add_argument('-o', '--output-dir', default='__pyspeedboost_bin__',
                               help='Output directory for compiled binaries')
    compile_parser.add_argument('-l', '--optimization-level', type=int, default=2,
                               help='Optimization level (0-3, higher = more optimization)')
    compile_parser.add_argument('-q', '--quiet', action='store_true',
                               help='Suppress compilation output')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run a script with binary acceleration')
    run_parser.add_argument('script', help='Python script to run')
    run_parser.add_argument('args', nargs=argparse.REMAINDER, help='Arguments to pass to the script')
    run_parser.add_argument('-q', '--quiet', action='store_true',
                           help='Suppress output')
    
    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Clean compiled binaries')
    clean_parser.add_argument('-a', '--all', action='store_true', 
                             help='Remove all compiled binaries')
    clean_parser.add_argument('-o', '--output-dir', default='__pyspeedboost_bin__',
                             help='Output directory to clean')
    
    # Version command
    subparsers.add_parser('version', help='Show version information')
    
    args = parser.parse_args()
    
    if args.command == 'compile':
        config = CompilerConfig(
            output_dir=args.output_dir,
            optimization_level=args.optimization_level,
            quiet_mode=args.quiet
        )
        compiler = PySpeedBoost(config)
        
        try:
            binary_path = compiler.compile(args.script, force=args.force)
            print(f"Successfully compiled {args.script} to {binary_path}")
        except CompilationError as e:
            print(f"Compilation failed: {e}")
            sys.exit(1)
    
    elif args.command == 'run':
        setup_logging(args.quiet)
        compiler = PySpeedBoost(CompilerConfig(quiet_mode=args.quiet))
        
        try:
            compiler.run(args.script, *args.args)
        except BinaryExecutionError as e:
            print(f"Execution failed: {e}")
            sys.exit(1)
    
    elif args.command == 'clean':
        import shutil
        try:
            if args.all:
                # Remove default output directory
                if os.path.exists('__pyspeedboost_bin__'):
                    shutil.rmtree('__pyspeedboost_bin__')
                    print("Removed default compiled binaries directory")
                
                # Also remove custom output directory if specified
                if args.output_dir != '__pyspeedboost_bin__' and os.path.exists(args.output_dir):
                    shutil.rmtree(args.output_dir)
                    print(f"Removed {args.output_dir}")
            else:
                # Clean only the specified directory
                if os.path.exists(args.output_dir):
                    shutil.rmtree(args.output_dir)
                    print(f"Cleaned {args.output_dir}")
                else:
                    print(f"Directory {args.output_dir} does not exist")
        except Exception as e:
            print(f"Clean failed: {e}")
            sys.exit(1)
    
    elif args.command == 'version':
        from . import __version__
        print(f"PySpeedBoost version {__version__}")
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()