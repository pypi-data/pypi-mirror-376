## mol-adme

mol-adme

Offline ADME & BOILED-Egg batch tool for molecules

mol-adme is a command-line tool that calculates ADME descriptors and generates BOILED-Egg plots from SMILES input.
It supports both individual and batch plots for multiple molecules, with customizable LogP options.


## **Installation**
Install directly via pip:
```bash
pip install mol-adme
```
This will install the CLI tool along with all dependencies (rdkit-pypi, pandas, matplotlib).


## **Usage**
Basic command
```bash
mol-adme --input molecules.smi
```

## **Options**

Option	      Description
--input	      Input SMILES file (.smi or .txt) with optional tags
--out	      CSV output file (default: results.csv)
--plots	      Generate individual BOILED-Egg plots for each molecule
--batchplot	  Generate a combined BOILED-Egg plot for all molecules
--plotdir	  Directory to save plots (default: plots)
--logptype	  LogP type for BOILED-Egg and CSV (WLogP or MolLogP)

## Example
```bash 
mol-adme --input molecules_example.smi --plots --batchplot --logptype MolLogP
```
This will generate:
results.csv → ADME descriptors for all molecules
plots/ → individual and batch BOILED-Egg plots

## SMILES Input Format
Each line in the .smi file should contain a SMILES string, optionally followed by tags for naming:

CC(=O)Oc1ccccc1C(=O)O Aspirin
C1=CC=CC=C1 Benzene

The tags after the SMILES string will be used to name individual plots and in the results CSV.

## Features

Calculates common ADME descriptors: MW, LogP, TPSA, HBD, HBA, RB
Lipinski & Veber rule assessment
Generates BOILED-Egg plots for predicting HIA (human intestinal absorption) and BBB (blood-brain barrier) penetration
Supports both individual molecule plots and batch plots
Customizable LogP type: WLogP (default) or MolLogP

