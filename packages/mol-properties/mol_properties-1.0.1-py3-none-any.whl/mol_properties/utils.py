# mol_properties/utils.py
from .calc import calc_properties

def process_inputs(input_path, strict_lipinski=False):
    results = []
    try:
        with open(input_path, "r") as f:
            for line in f:
                parts = line.strip().split(maxsplit=1)
                if not parts:
                    continue
                smiles = parts[0]
                tag = parts[1] if len(parts) > 1 else None
                props = calc_properties(smiles, tag, strict_lipinski)
                if props:
                    results.append(props)
    except FileNotFoundError:
        props = calc_properties(input_path, strict_lipinski=strict_lipinski)
        if props:
            results.append(props)
    return results
