#!/usr/bin/env python3
"""
InvoiceAgent Package Builder

This script builds and uploads the InvoiceAgent package to PyPI or TestPyPI.
Usage:
    python build_package.py [test|prod]
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Configuration
PACKAGE_NAME = "invoiceagent"
DIST_DIR = "dist"
BUILD_DIR = "build"
TEST_PYPI_REPO = "https://test.pypi.org/legacy/"

def clean_build_directories():
    """Remove build artifacts from previous builds."""
    print("Cleaning build directories...")
    for directory in [DIST_DIR, BUILD_DIR, f"{PACKAGE_NAME}.egg-info"]:
        if os.path.exists(directory):
            shutil.rmtree(directory)
            print(f"  Removed {directory}")

def build_package():
    """Build source distribution and wheel."""
    print("\nBuilding package...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "build", "twine"], check=True)
    subprocess.run([sys.executable, "-m", "build"], check=True)
    
    # List built packages
    print("\nBuilt packages:")
    for file in os.listdir(DIST_DIR):
        print(f"  {file}")

def upload_to_pypi(test=True):
    """Upload the package to PyPI or TestPyPI."""
    if test:
        print("\nUploading to TestPyPI...")
        cmd = [
            sys.executable, "-m", "twine", "upload", 
            "--repository-url", TEST_PYPI_REPO,
            f"{DIST_DIR}/*"
        ]
    else:
        print("\nUploading to PyPI...")
        cmd = [sys.executable, "-m", "twine", "upload", f"{DIST_DIR}/*"]
        
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode != 0:
        print("\nUpload failed. Make sure you have set up your PyPI credentials.")
        print("You can set up credentials in ~/.pypirc or through environment variables:")
        print("  export TWINE_USERNAME=your_username")
        print("  export TWINE_PASSWORD=your_password")
        sys.exit(1)
    
    print("Upload completed successfully!")
    
    if test:
        print("\nTo test installation, run:")
        print(f"pip install --index-url {TEST_PYPI_REPO} --extra-index-url https://pypi.org/simple/ {PACKAGE_NAME}")
    else:
        print(f"\nPackage published! Users can now install with: pip install {PACKAGE_NAME}")

def main():
    """Main entry point."""
    # Determine target repository
    target = "test"
    if len(sys.argv) > 1:
        target = sys.argv[1].lower()
    
    # Validate target
    if target not in ["test", "prod"]:
        print("Error: Invalid target. Use 'test' for TestPyPI or 'prod' for PyPI.")
        sys.exit(1)
    
    # Execute build and upload steps
    clean_build_directories()
    build_package()
    upload_to_pypi(test=(target == "test"))
    
    print("\nProcess completed!")

if __name__ == "__main__":
    main() 