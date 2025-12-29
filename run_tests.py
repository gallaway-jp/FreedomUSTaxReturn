"""
Test runner script for FreedomUSTaxReturn
Runs pytest with appropriate options
"""
import sys
import subprocess


def main():
    """Run tests with pytest"""
    
    # Default pytest arguments
    args = [
        'pytest',
        '-v',                  # Verbose
        '--tb=short',         # Short traceback format
        '--color=yes',        # Colored output
    ]
    
    # Add coverage if requested
    if '--cov' in sys.argv or '--coverage' in sys.argv:
        args.extend([
            '--cov=models',
            '--cov=utils',
            '--cov-report=html',
            '--cov-report=term-missing',
        ])
        sys.argv = [arg for arg in sys.argv if arg not in ['--cov', '--coverage']]
    
    # Add any additional arguments passed to this script
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])
    
    # Run pytest
    print("Running tests...")
    print(f"Command: {' '.join(args)}")
    print("-" * 80)
    
    result = subprocess.run(args)
    
    # Exit with same code as pytest
    sys.exit(result.returncode)


if __name__ == '__main__':
    main()
