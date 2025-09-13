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

```bash
pip install mol-properties
```

## Usage 
Single molecule 
```bash
mol-properties "CCO" -o ethanol.csv
```

Multiple molecules from a file eg: molecules.smi
```bash 
mol-properties molecules.smi -o output.csv
```

Strict Lipinski mode
```bash 
mol-properties molecules.smi -o output.csv --strict-lipinski
```


## Output 
-CSV file with molecular properties 
-Summary printed in terminal -> Number of molecules passing Lipinski and Veber rules.

## Dependencies
-Python >= 3.10
-RDKit
-pandas
