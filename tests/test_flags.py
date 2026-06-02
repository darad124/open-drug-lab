from opendruglab.models import DescriptorRecord
from opendruglab.workflow import rule_flags


def test_rule_flags_warn_for_lipinski_style_thresholds() -> None:
    descriptor = DescriptorRecord(
        molecule_id="large",
        input_smiles="C",
        canonical_smiles="C",
        molecular_weight=650,
        clogp=6.2,
        tpsa=30,
        hbd=1,
        hba=2,
        rotatable_bonds=12,
        ring_count=1,
        formal_charge=0,
        qed=0.2,
    )

    flags = rule_flags(descriptor)

    assert {flag.flag for flag in flags} == {
        "mw_gt_500",
        "clogp_gt_5",
        "rotatable_bonds_gt_10",
    }


def test_rule_flags_add_info_when_no_thresholds_fail() -> None:
    descriptor = DescriptorRecord(
        molecule_id="ethanol",
        input_smiles="CCO",
        canonical_smiles="CCO",
        molecular_weight=46.069,
        clogp=-0.001,
        tpsa=20.23,
        hbd=1,
        hba=1,
        rotatable_bonds=0,
        ring_count=0,
        formal_charge=0,
        qed=0.407,
    )

    flags = rule_flags(descriptor)

    assert len(flags) == 1
    assert flags[0].flag == "no_basic_rule_flags"
