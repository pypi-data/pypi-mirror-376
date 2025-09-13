![PyPI](https://img.shields.io/pypi/v/mol-properties)
![Python Version](https://img.shields.io/pypi/pyversions/mol-properties)
![License](https://img.shields.io/pypi/l/mol-properties)
[![Code of Conduct](https://img.shields.io/badge/Code%20of%20Conduct-Contributor%20Covenant-4baaaa.svg)](CODE_OF_CONDUCT.md)
[![Contributors](https://img.shields.io/badge/Contributing-Yes-brightgreen.svg)](CONTRIBUTING.md)
[![Security Policy](https://img.shields.io/badge/Security-Policy-green)](https://github.com/<USERNAME>/<REPO>/security/policy)
[![Contributing](https://img.shields.io/badge/Contributing-guidelines-blue)](https://github.com/<USERNAME>/<REPO>/blob/main/CONTRIBUTING.md)


# mol-properties

**mol-properties** is a Python CLI tool to calculate molecular properties and evaluate drug-likeness rules (Lipinski & Veber). It also predicts approximate aqueous solubility (logS) using the ESOL model.

## Features

- Calculate key molecular descriptors:
  - Molecular Weight (MW)
  - LogP
  - H-bond donors (HBD)
  - H-bond acceptors (HBA)
  - Topological Polar Surface Area (TPSA)
  - Rotatable Bonds (RotB)
  - LogS (aqueous solubility)
- Check Lipinski and Veber rules for drug-likeness.
- Accepts **single SMILES** or **file containing multiple SMILES**.
- Optional strict Lipinski mode: any violation fails.



## Installation

This package requires [RDKit](https://www.rdkit.org/), which is not always available on PyPI.  
Please install RDKit first:

- Using conda (recommended):
  ```bash
  conda install -c conda-forge rdkit

``` 
or via pip (Linux / macOS only):
```bash
pip install rdkit
```

then install mol-properties
```bash
pip install mol-properties
