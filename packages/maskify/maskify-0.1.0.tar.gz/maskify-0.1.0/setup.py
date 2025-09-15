import os
from setuptools import setup, find_packages

# Get the directory where setup.py is located
here = os.path.abspath(os.path.dirname(__file__))

# Read the README file for the long description
with open(os.path.join(here, "README.md"), "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="maskify",
    version="0.1.0",
    description="A simple tool to mask sensitive columns in .csv and .dat files.",
    author="Vikas Bhaskar Vooradi",
    author_email="vikasvooradi.developer@gmail.com",
    packages=find_packages(),
    install_requires=[
        "polars>=1.25.2",
    ],
    python_requires=">=3.12.11",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    license_files=("LICENSE",),
)
