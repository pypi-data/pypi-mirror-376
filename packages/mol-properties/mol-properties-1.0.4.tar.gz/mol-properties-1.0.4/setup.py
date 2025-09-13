from setuptools import setup, find_packages

setup(
    name="mol-properties",  # This is the PyPI name
    version="1.0.4",  
    author="Your Name",
    author_email="your.email@example.com",
    description="CLI tool to calculate molecular properties and drug-likeness",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mol-properties",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "pandas",
    ],
    entry_points={
        "console_scripts": [
            "mol-properties = mol_properties.__main__:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
