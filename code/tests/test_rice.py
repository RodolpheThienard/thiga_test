import pytest
from agent.rice import score_rice, impact_base, controler_impact, controler_confidence, controler_effort


def test_poids_a_un_donne_le_rice_classique():
    assert score_rice(6, 3, 100, 5) == pytest.approx(6 * 3 * 1.0 / 5)
    assert score_rice(4, 2, 80, 8) == pytest.approx(4 * 2 * 0.8 / 8)


def test_un_poids_plus_fort_renforce_le_critere():
    sans = score_rice(4, 2, 80, 8)
    avec = score_rice(4, 2, 80, 8, poids_reach=2)
    assert avec == pytest.approx(sans * 4)


def test_poids_effort_nul_ignore_l_effort():
    assert score_rice(2, 1, 100, 21, poids_effort=0) == pytest.approx(2)


def test_effort_nul_refuse():
    with pytest.raises(ValueError):
        score_rice(1, 1, 100, 0)


def test_bareme_fixe_de_gravite():
    assert [impact_base(g) for g in ["Bloquant", "Majeur", "Mineur", "Cosmétique"]] == [3, 2, 1, 0.5]


@pytest.mark.parametrize("base,propose,attendu,signal", [
    (2.0, 2.0, 2.0, False), (2.0, 3.0, 3.0, False), (2.0, 1.0, 1.0, False),
    (1.0, 3.0, 1.0, True),    # deux crans : refusé
    (2.0, 1.5, 2.0, True),    # hors échelle
])
def test_controle_impact_un_cran_maximum(base, propose, attendu, signal):
    valeur, alerte = controler_impact(base, propose)
    assert valeur == attendu and (alerte is not None) == signal


def test_confidence_hors_echelle_ramenee():
    assert controler_confidence(80) == (80, None)
    assert controler_confidence(70)[0] == 80


def test_effort_fibonacci_et_backlog_repris():
    assert controler_effort(5) == (5, None)
    assert controler_effort(6)[0] == 5
    assert controler_effort(8, estimation_backlog=13)[0] == 13
