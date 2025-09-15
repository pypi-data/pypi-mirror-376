#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path
import argparse

def run_command(command, cwd=None):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            capture_output=True, 
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"Error: {e.stderr}"

def process_python_file(file_path):
    """Process a single Python file with the specified commands"""
    print(f"Processing: {file_path}")
    
    # Command 1: isort
    print(f"  Running isort on {file_path}...")
    success, output = run_command(f"isort '{file_path}'")
    if not success:
        print(f"    ⚠️  isort failed: {output}")
    else:
        print(f"    ✅ isort completed")
    
    # Command 2: black
    print(f"  Running black on {file_path}...")
    success, output = run_command(f"black '{file_path}'")
    if not success:
        print(f"    ⚠️  black failed: {output}")
    else:
        print(f"    ✅ black completed")
    
    print()

def process_single_file(file_path):
    """Process a single specified file"""
    file_path = Path(file_path).resolve()
    
    # Check if file exists
    if not file_path.exists():
        print(f"❌ Error: File '{file_path}' does not exist.")
        return False
    
    # Check if it's a Python file
    if file_path.suffix != '.py':
        print(f"❌ Error: '{file_path}' is not a Python file (.py).")
        return False
    
    print(f"Single file mode: Processing {file_path}")
    print("=" * 50)
    
    process_python_file(file_path)
    
    print("=" * 50)
    print("✅ File processed successfully!")
    return True

def process_bulk_files():
    """Process all Python files in current directory and subdirectories"""
    # Get current working directory (where command is run)
    current_dir = Path.cwd()
    print(f"Bulk mode: Processing all .py files in: {current_dir}")
    print("=" * 50)
    
    # Find all Python files recursively
    python_files = list(current_dir.rglob("*.py"))
    python_files.sort()
    
    if not python_files:
        print("No Python files found to process.")
        return
    
    print(f"Found {len(python_files)} Python files to process:")
    for file_path in python_files:
        print(f"  - {file_path.relative_to(current_dir)}")
    print()
    
    # Ask for confirmation
    response = input("Do you want to proceed? (y/N): ").strip().lower()
    if response != 'y':
        print("Operation cancelled.")
        return
    
    print("\nStarting processing...")
    print("=" * 50)
    
    # Process each file
    for file_path in python_files:
        process_python_file(file_path)
    
    print("=" * 50)
    print("✅ All files processed!")

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Format Python files using isort and black",
        epilog="""
Examples:
  make-pretty                    # Process all .py files in current directory (bulk mode)
  make-pretty script.py          # Process a single file
  make-pretty src/main.py        # Process a single file with path
  make-pretty /path/to/file.py   # Process a single file with absolute path
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'file', 
        nargs='?',
        help='Path to a specific Python file to process. If not provided, processes all .py files in current directory.'
    )
    
    parser.add_argument(
        '--version', 
        action='version', 
        version='make-pretty 2.0'
    )
    
    args = parser.parse_args()
    
    # Check if required tools are available
    for tool in ['isort', 'black']:
        success, _ = run_command(f"which {tool}")
        if not success:
            print(f"❌ Error: '{tool}' is not installed or not found in PATH.")
            print(f"Please install it using: pip install {tool}")
            sys.exit(1)
    
    if args.file:
        # Single file mode
        success = process_single_file(args.file)
        if not success:
            sys.exit(1)
    else:
        # Bulk mode (original behavior)
        process_bulk_files()

if __name__ == "__main__":
    main()