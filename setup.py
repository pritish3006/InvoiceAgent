from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="invoiceagent",
    version="0.1.0",
    author="Pritish Mishra",
    author_email="your.email@example.com",
    description="A lightweight, AI-powered invoicing system for independent contractors",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pritish3006/InvoiceAgent",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
    ],
    python_requires=">=3.12",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "invoiceagent=invoiceagent.cli:main",
        ],
    },
) 