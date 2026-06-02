DESCRIPTOR_EXPLANATIONS = [
    {
        "name": "Molecular weight",
        "key": "MW",
        "description": (
            "Approximate mass of the molecule. Very high values can reduce "
            "oral drug-likeness in simple screening rules."
        ),
    },
    {
        "name": "cLogP",
        "key": "cLogP",
        "description": (
            "Estimated lipophilicity. Higher values suggest a molecule may "
            "prefer oily environments over water."
        ),
    },
    {
        "name": "TPSA",
        "key": "TPSA",
        "description": (
            "Topological polar surface area. This rough signal is often "
            "discussed when thinking about permeability."
        ),
    },
    {
        "name": "HBD / HBA",
        "key": "HBD/HBA",
        "description": (
            "Hydrogen bond donors and acceptors. Simple rules use these as "
            "rough interaction and permeability signals."
        ),
    },
    {
        "name": "Rotatable bonds",
        "key": "RotB",
        "description": (
            "A rough flexibility measure. Highly flexible molecules can be "
            "harder to optimize."
        ),
    },
    {
        "name": "QED",
        "key": "QED",
        "description": (
            "A heuristic RDKit score summarizing several drug-likeness-like "
            "properties. It is not a safety or efficacy prediction."
        ),
    },
]
