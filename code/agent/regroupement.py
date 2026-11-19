"""P2 – Regroupement en thèmes, et contrôles par le code."""
from __future__ import annotations

import json

from .schemas import ReponseP2

THEME_NON_REGROUPE = "Demandes non regroupées par l'agent"


def controler_regroupement(themes: list[dict], ids_attendus: list[str]) -> tuple[list[dict], list[str]]:
    """Chaque demande doit apparaître dans exactement un thème.

    - identifiant inconnu : retiré ;
    - doublon : conservé dans le premier thème, retiré des suivants ;
    - demande oubliée : placée dans un thème « non regroupé ».
    Les thèmes vides sont supprimés. Renvoie (thèmes corrigés, alertes).
    """
    attendus = set(ids_attendus)
    vus: set[str] = set()
    alertes: list[str] = []
    corriges = []
    for t in themes:
        gardees = []
        for d in t["demandes"]:
            if d not in attendus:
                alertes.append(f"Identifiant de demande inconnu ignoré : {d}.")
            elif d in vus:
                alertes.append(f"La demande {d} figurait dans plusieurs thèmes : conservée dans le premier.")
            else:
                vus.add(d)
                gardees.append(d)
        if gardees:
            corriges.append({**t, "demandes": gardees})
    oubliees = [d for d in ids_attendus if d not in vus]
    if oubliees:
        alertes.append(f"{len(oubliees)} demande(s) non regroupée(s) par l'agent : {', '.join(oubliees)}.")
        corriges.append({
            "titre": THEME_NON_REGROUPE, "description": "Demandes que l'agent n'a rattachées à aucun thème.",
            "demandes": oubliees, "backlog_id": None, "couverture_backlog": None,
            "hors_vision": False, "justification": "Ajouté par le contrôle du code.",
        })
    for i, t in enumerate(corriges, start=1):
        t["theme_id"] = f"TH-{i}"
    return corriges, alertes


def regrouper(client, contexte: str, demandes: dict[str, dict], feedbacks: dict[str, dict], backlog: list[dict]) -> tuple[list[dict], list[str]]:
    lignes = []
    for id_d, d in demandes.items():
        fb = feedbacks[d["feedback_id"]]
        lignes.append({
            "id_demande": id_d, "probleme": d["probleme"], "gravite": d["gravite"],
            "enjeu_business": d["enjeu_business"], "hors_vision": d["hors_vision"],
            "date": fb["date"], "canal": fb["canal"],
        })
    backlog_court = [{k: b[k] for k in ("id", "titre", "description", "statut")} for b in backlog]
    message = (
        "Demandes à regrouper :\n" + json.dumps(lignes, ensure_ascii=False, indent=1)
        + "\n\nBacklog existant :\n" + json.dumps(backlog_court, ensure_ascii=False, indent=1)
    )
    reponse = client.appeler("P2_regroupement", contexte, message, ReponseP2, temperature=0)
    themes = [t.model_dump() for t in reponse.themes]
    return controler_regroupement(themes, list(demandes))
