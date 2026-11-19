"""R7 – Répartition MoSCoW, calculée par des règles fixes et paramétrables."""
from __future__ import annotations

MUST, SHOULD, COULD, WONT = "Must", "Should", "Could", "Won't"


def repartir(themes: list[dict], capacite: int = 35, regle_bloquant_retention: bool = True,
             horizon_should_sprints: int = 1) -> dict:
    """Répartit les thèmes.

    Chaque thème : {theme_id, score, effort, gravite_max, enjeux, hors_vision, force (catégorie ou None)}.
    Renvoie {"categories": {theme_id: {"categorie", "regle_appliquee"}}, "points_must", "points_should", "alertes"}.
    """
    categories: dict[str, dict] = {}
    points_must = 0
    points_should = 0
    capacite_should = capacite * horizon_should_sprints
    alertes: list[str] = []

    restants = []
    # 1. Choix forcés par le PO : prioritaires sur toute règle.
    for t in themes:
        if t.get("force"):
            categories[t["theme_id"]] = {"categorie": t["force"], "regle_appliquee": "Catégorie choisie par le PO"}
            if t["force"] == MUST:
                points_must += t["effort"]
            elif t["force"] == SHOULD:
                points_should += t["effort"]
        elif t.get("hors_vision"):
            categories[t["theme_id"]] = {"categorie": WONT, "regle_appliquee": "Hors vision produit"}
        else:
            restants.append(t)

    # 2. Bloquant + Rétention : Must d'office (règle activable).
    if regle_bloquant_retention:
        for t in list(restants):
            if t.get("gravite_max") == "Bloquant" and "Rétention" in (t.get("enjeux") or []):
                categories[t["theme_id"]] = {"categorie": MUST, "regle_appliquee": "Bloquant à enjeu Rétention : Must d'office"}
                points_must += t["effort"]
                restants.remove(t)

    if points_must > capacite:
        alertes.append(
            f"Les Must imposés (règle Bloquant + Rétention ou choix du PO) représentent {points_must} points, "
            f"au-delà de la capacité du sprint ({capacite} points)."
        )

    # 3. Les autres, par score décroissant, dans la limite des capacités.
    for t in sorted(restants, key=lambda x: x["score"], reverse=True):
        if points_must + t["effort"] <= capacite:
            categories[t["theme_id"]] = {"categorie": MUST, "regle_appliquee": "Score élevé, rentre dans la capacité du sprint"}
            points_must += t["effort"]
        elif points_should + t["effort"] <= capacite_should:
            categories[t["theme_id"]] = {"categorie": SHOULD, "regle_appliquee": "Ne rentre pas dans le sprint, rentre dans l'horizon Should"}
            points_should += t["effort"]
        else:
            categories[t["theme_id"]] = {"categorie": COULD, "regle_appliquee": "Au-delà de la capacité des sprints à venir"}

    return {"categories": categories, "points_must": points_must, "points_should": points_should, "alertes": alertes}
