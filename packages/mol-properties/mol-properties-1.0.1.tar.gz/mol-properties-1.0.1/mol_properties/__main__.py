# mol_properties/__main__.py
import argparse
import pandas as pd
from .utils import process_inputs

def main():
    parser = argparse.ArgumentParser(description="Molecule property calculator with drug-likeness rules")
    parser.add_argument("input", help="SMILES string or a file containing SMILES (optionally with names)")
    parser.add_argument("-o", "--output", default="properties.csv", help="Output CSV file")
    parser.add_argument("--strict-lipinski", action="store_true", help="Use strict Lipinski interpretation (any violation = fail)")
    args = parser.parse_args()

    results = process_inputs(args.input, strict_lipinski=args.strict_lipinski)
    if not results:
        print("❌ No valid molecules processed.")
        return

    df = pd.DataFrame(results)
    df.to_csv(args.output, index=False)

    # Print summary
    lip_pass = df["Lipinski_pass"].sum()
    veb_pass = df["Veber_pass"].sum()
    total = len(df)

    print(f"✅ Saved {total} records to {args.output}")
    print(f"🔹 Lipinski pass: {lip_pass}/{total}")
    print(f"🔹 Veber pass: {veb_pass}/{total}")

if __name__ == "__main__":
    main()
