#!/usr/bin/env python3
import os
import argparse
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit.Chem.Crippen import MolLogP
from rdkit.Chem.rdMolDescriptors import CalcTPSA
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

# ----------------------------
# Descriptor calculation
# ----------------------------
def calc_descriptors(mol, logptype="WLogP"):
    desc = {}
    desc['MW'] = Descriptors.MolWt(mol)
    # LogP choice
    if logptype == "MolLogP":
        desc['LogP'] = Descriptors.MolLogP(mol)
    else:
        desc['LogP'] = MolLogP(mol)  # WLogP
    desc['TPSA'] = CalcTPSA(mol)
    desc['HBD'] = Descriptors.NumHDonors(mol)
    desc['HBA'] = Descriptors.NumHAcceptors(mol)
    desc['RB'] = Descriptors.NumRotatableBonds(mol)
    # Lipinski Rule
    desc['Lipinski'] = 'Pass' if (desc['MW'] <= 500 and desc['HBD'] <=5 and desc['HBA'] <=10 and desc['LogP'] <=5) else 'Fail'
    # Veber Rule
    desc['Veber'] = 'Pass' if (desc['TPSA'] <=140 and desc['RB'] <=10) else 'Fail'
    return desc

# ----------------------------
# BOILED-Egg plot (single molecule)
# ----------------------------
def plot_boiled_egg(desc, name, outdir, logtype_name):
    fig, ax = plt.subplots(figsize=(5,5))
    ax.set_xlim(-3, 10)
    ax.set_ylim(0, 160)
    ax.set_xlabel(f"{logtype_name}")
    ax.set_ylabel("TPSA")
    ax.set_title(f"BOILED-Egg: {name}")

    # Egg white (HIA)
    white = Ellipse((2.5, 65), width=8, height=130, color='white', alpha=0.3, label='HIA')
    ax.add_patch(white)

    # Yolk (BBB)
    yolk = Ellipse((2.5, 45), width=6, height=90, color='yellow', alpha=0.4, label='BBB')
    ax.add_patch(yolk)

    # Plot molecule
    ax.scatter(desc['LogP'], desc['TPSA'], color='red', s=100, label=name, zorder=5)
    ax.legend()
    plt.tight_layout()

    os.makedirs(outdir, exist_ok=True)
    plot_path = os.path.join(outdir, f"{name}.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    return plot_path

# ----------------------------
# BOILED-Egg batch plot (all molecules)
# ----------------------------
def plot_batch_egg(results, outdir, logtype_name):
    fig, ax = plt.subplots(figsize=(7,7))
    ax.set_xlim(-3, 10)
    ax.set_ylim(0, 160)
    ax.set_xlabel(f"{logtype_name}")
    ax.set_ylabel("TPSA")
    ax.set_title("BOILED-Egg: Batch Plot")

    # Egg white (HIA)
    white = Ellipse((2.5, 65), width=8, height=130, color='white', alpha=0.3, label='HIA')
    ax.add_patch(white)

    # Yolk (BBB)
    yolk = Ellipse((2.5, 45), width=6, height=90, color='yellow', alpha=0.4, label='BBB')
    ax.add_patch(yolk)

    # Color map for points and labels (Matplotlib 3.11+)
    n = len(results)
    cmap = plt.get_cmap('tab20', n)

    # Plot all molecules with colored points and matching labels
    for i, res in enumerate(results):
        x = res['LogP']
        y = res['TPSA']
        color = cmap(i)  # unique color per molecule
        ax.scatter(x, y, s=100, color=color, zorder=5)
        # Offset labels slightly to prevent overlap
        offset_x = 0.3 if i % 2 == 0 else -0.3
        offset_y = 2 if i % 2 == 0 else -2
        ax.text(x + offset_x, y + offset_y, res['Name'], fontsize=8, color=color)

    ax.legend()
    plt.tight_layout()

    os.makedirs(outdir, exist_ok=True)
    batch_plot_path = os.path.join(outdir, "batch_boiled_egg.png")
    plt.savefig(batch_plot_path, dpi=300)
    plt.close()
    print(f"📊 Batch BOILED-Egg plot saved → {batch_plot_path}")

# ----------------------------
# Main function
# ----------------------------
def main():
    parser = argparse.ArgumentParser(description="mol-adme: Offline ADME & BOILED-Egg batch tool")
    parser.add_argument("--input", required=True, help="Input SMILES file (.smi or .txt) with optional tags")
    parser.add_argument("--out", default="results.csv", help="CSV output file")
    parser.add_argument("--plots", action="store_true", help="Generate individual BOILED-Egg plots")
    parser.add_argument("--batchplot", action="store_true", help="Generate one combined BOILED-Egg plot for all molecules")
    parser.add_argument("--plotdir", default="plots", help="Directory to save plots")
    parser.add_argument("--logptype", default="WLogP", choices=["WLogP","MolLogP"], help="LogP type for BOILED-Egg plot and CSV")
    args = parser.parse_args()

    logtype_name = args.logptype

    # Create plot directory if needed
    if args.plots or args.batchplot:
        os.makedirs(args.plotdir, exist_ok=True)

    # Read SMILES file
    molecules = []
    with open(args.input, 'r') as f:
        for idx, line in enumerate(f.readlines()):
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            smiles = parts[0]
            name = "_".join(parts[1:]) if len(parts) > 1 else f"mol_{idx+1}"
            molecules.append((smiles, name))

    if not molecules:
        print("⚠️ No valid SMILES found in input file.")
        return

    # Process molecules
    results = []
    for smiles, name in molecules:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            print(f"⚠️  Failed to parse SMILES: {smiles} ({name})")
            continue
        desc = calc_descriptors(mol, logptype=args.logptype)
        desc['SMILES'] = smiles
        desc['Name'] = name
        if args.plots:
            print(f"📊 Generating BOILED-Egg for {name}")
            plot_path = plot_boiled_egg(desc, name, args.plotdir, logtype_name)
            desc['Plot'] = plot_path
        results.append(desc)
        print(f"✅ Processed: {name}")

    # Save CSV
    df = pd.DataFrame(results)
    cols = ['Name','SMILES','MW','LogP','TPSA','HBD','HBA','RB','Lipinski','Veber']
    if args.plots:
        cols.append('Plot')
    df = df[cols]
    df.to_csv(args.out, index=False)
    print(f"📄 Results saved to {args.out}")

    # Batch plot
    if args.batchplot and results:
        plot_batch_egg(results, args.plotdir, logtype_name)

if __name__ == "__main__":
    main()
