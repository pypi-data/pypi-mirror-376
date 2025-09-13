# mol_properties/calc.py
from rdkit import Chem
from rdkit.Chem import Descriptors, Crippen, Lipinski, rdMolDescriptors

def calc_logS(mol):
    """Approximate aqueous solubility (logS) using ESOL model."""
    if mol is None:
        return None
    mw = Descriptors.MolWt(mol)
    logp = Crippen.MolLogP(mol)
    rotb = Lipinski.NumRotatableBonds(mol)
    tpsa = rdMolDescriptors.CalcTPSA(mol)
    logS = 0.16 - 0.63*logp - 0.0062*mw + 0.066*rotb + 0.74*(tpsa/100.0)
    return round(logS, 2)

def calc_properties(smiles, tag=None, strict_lipinski=False):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    mw = Descriptors.MolWt(mol)
    logp = Crippen.MolLogP(mol)
    hbd = Lipinski.NumHDonors(mol)
    hba = Lipinski.NumHAcceptors(mol)
    tpsa = rdMolDescriptors.CalcTPSA(mol)
    rotb = Lipinski.NumRotatableBonds(mol)
    logS = calc_logS(mol)

    # Lipinski checks
    lip_reasons = []
    if mw > 500: lip_reasons.append(f"MW>{500}")
    if logp > 5: lip_reasons.append(f"LogP>{5:.1f}")
    if hbd > 5: lip_reasons.append(f"HBD>{5}")
    if hba > 10: lip_reasons.append(f"HBA>{10}")
    lip_violations = len(lip_reasons)
    lipinski_pass = (lip_violations == 0) if strict_lipinski else (lip_violations <= 1)

    # Veber checks
    veber_reasons = []
    if tpsa > 140: veber_reasons.append(f"TPSA>{140}")
    if rotb > 10: veber_reasons.append(f"RotB>{10}")
    veber_pass = (len(veber_reasons) == 0)

    return {
        "Name_or_ID": tag if tag else smiles,
        "SMILES": smiles,
        "MW": round(mw, 3),
        "LogP": round(logp, 2),
        "logS": logS,
        "HBD": hbd,
        "HBA": hba,
        "TPSA": round(tpsa, 1),
        "RotB": rotb,
        "Lipinski_pass": lipinski_pass,
        "Lipinski_violations": lip_violations,
        "Lipinski_fail_reasons": ";".join(lip_reasons) if lip_reasons else "",
        "Veber_pass": veber_pass,
        "Veber_fail_reasons": ";".join(veber_reasons) if veber_reasons else ""
    }
