"""RDKit-Helfer: Summenformel und exakte Masse aus SMILES."""


def compute_from_smiles(smiles: str) -> tuple[str, float]:
    """Gibt (Summenformel, exakte Masse) zurück. ValueError bei ungültigem SMILES."""
    from rdkit import Chem
    from rdkit.Chem.Descriptors import ExactMolWt
    from rdkit.Chem.rdMolDescriptors import CalcMolFormula

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(smiles)
    return CalcMolFormula(mol), round(ExactMolWt(mol), 4)
