from agent.moscow import repartir


def th(i, score, effort, gravite="Majeur", enjeux=("Efficacité",), hv=False, force=None):
    return {"theme_id": i, "score": score, "effort": effort, "gravite_max": gravite,
            "enjeux": list(enjeux), "hors_vision": hv, "force": force}


def cats(r):
    return {k: v["categorie"] for k, v in r["categories"].items()}


def test_hors_vision_en_wont():
    assert cats(repartir([th("A", 99, 1, hv=True)]))["A"] == "Won't"


def test_bloquant_retention_must_d_office_meme_score_faible():
    r = repartir([th("A", 10, 20), th("B", 0.1, 13, "Bloquant", ["Rétention"])], capacite=20)
    assert cats(r) == {"B": "Must", "A": "Should"}


def test_regle_bloquant_desactivable():
    r = repartir([th("A", 10, 20), th("B", 0.1, 13, "Bloquant", ["Rétention"])], capacite=20, regle_bloquant_retention=False)
    assert cats(r) == {"A": "Must", "B": "Should"}


def test_capacite_respectee_par_score_decroissant():
    r = repartir([th("A", 5, 20), th("B", 4, 20), th("C", 3, 10), th("D", 1, 40)], capacite=35)
    assert cats(r) == {"A": "Must", "C": "Must", "B": "Should", "D": "Could"}
    assert r["points_must"] == 30


def test_horizon_should():
    themes = [th("A", 5, 30), th("B", 4, 30), th("C", 3, 30)]
    assert cats(repartir(themes, capacite=35, horizon_should_sprints=1))["C"] == "Could"
    assert cats(repartir(themes, capacite=35, horizon_should_sprints=2))["C"] == "Should"


def test_alerte_si_must_imposes_depassent_capacite():
    r = repartir([th("A", 1, 21, "Bloquant", ["Rétention"]), th("B", 1, 21, "Bloquant", ["Rétention"])], capacite=35)
    assert r["alertes"] and r["points_must"] == 42


def test_forcage_par_le_po_prioritaire():
    r = repartir([th("A", 1, 5, hv=True, force="Should"), th("B", 99, 5, force="Could")])
    assert cats(r) == {"A": "Should", "B": "Could"}
    assert r["categories"]["B"]["regle_appliquee"] == "Catégorie choisie par le PO"
