#!/usr/bin/env python3
"""
InvoiceAgent setup script for backward compatibility.
Modern Python packaging uses pyproject.toml, but setup.py is included for
compatibility with older tools and environments.
"""

from setuptools import find_packages, setup


# Read requirements from requirements.txt
def read_requirements():
    """Read requirements from requirements.txt file."""
    with open("requirements.txt", "r", encoding="utf-8") as req_file:
        return [line.strip() for line in req_file if line.strip() and not line.startswith("#")]


# Read long description from README.md
def read_long_description():
    """Read long description from README.md."""
    with open("README.md", "r", encoding="utf-8") as readme_file:
        return readme_file.read()


# Main setup configuration
if __name__ == "__main__":
    setup(
        name="invoiceagent",
        version="0.1.0",
        description="A CLI application for managing clients, tracking work, generating invoices, and exporting to PDF",
        long_description=read_long_description(),
        long_description_content_type="text/markdown",
        author="Pritish Mishra",
        author_email="example@example.com",
        url="https://github.com/yourusername/invoiceagent",
        packages=find_packages(),
        include_package_data=True,
        install_requires=read_requirements(),
        entry_points={
            "console_scripts": [
                "invoiceagent=invoiceagent.cli.main:main",
            ],
        },
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Environment :: Console",
            "Intended Audience :: Freelancers",
            "License :: OSI Approved :: MIT License",
            "Natural Language :: English",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
            "Topic :: Office/Business :: Financial :: Accounting",
        ],
        python_requires=">=3.10",
    )
