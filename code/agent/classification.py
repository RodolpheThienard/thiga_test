"""P1 – Classification des feedbacks, par lots, et filtrage (R3)."""
from __future__ import annotations

import json

from .config import CATEGORIES_ECARTEES, TAILLE_LOT_P1
from .schemas import ReponseP1


def _message_lot(lot: list[dict], reintegres: set[str]) -> str:
    # L'auteur et l'email ne sont pas transmis : inutiles pour classer (données personnelles).
    lignes = [{k: f.get(k) for k in ("id", "canal", "date", "objet", "contenu")} for f in lot]
    message = "Voici les feedbacks à qualifier :\n" + json.dumps(lignes, ensure_ascii=False, indent=1)
    forces = [f["id"] for f in lot if f["id"] in reintegres]
    if forces:
        message += (
            "\n\nLe Product Owner a indiqué que les feedbacks suivants sont actionnables : "
            + ", ".join(forces) + ". Propose au moins une demande pour chacun."
        )
    return message


def classer(client, contexte: str, feedbacks: list[dict], reintegres: set[str] | None = None,
            progression=None) -> tuple[dict[str, dict], list[str]]:
    """Renvoie (fiches par id de feedback, alertes)."""
    reintegres = reintegres or set()
    fiches: dict[str, dict] = {}
    alertes: list[str] = []
    lots = [feedbacks[i:i + TAILLE_LOT_P1] for i in range(0, len(feedbacks), TAILLE_LOT_P1)]
    for n, lot in enumerate(lots, start=1):
        if progression:
            progression(f"Classification des feedbacks (lot {n}/{len(lots)})")
        reponse = client.appeler("P1_classification", contexte, _message_lot(lot, reintegres), ReponseP1, temperature=0)
        ids_lot = {f["id"] for f in lot}
        for fiche in reponse.fiches:
            if fiche.id in ids_lot:
                fiches[fiche.id] = fiche.model_dump()
        manquants = ids_lot - {f.id for f in reponse.fiches}
        for id_m in sorted(manquants):
            alertes.append(f"{id_m} n'a pas été classé par l'agent : conservé comme Question/Support à vérifier.")
            fiches[id_m] = {"id": id_m, "categorie": "Question/Support", "demandes": [],
                            "justification": "Non classé par l'agent (ajouté par le contrôle du code)."}
    # Cohérence : une catégorie écartée n'a pas de demande, sauf réintégration par le PO.
    for id_f, fiche in fiches.items():
        if fiche["categorie"] in CATEGORIES_ECARTEES and id_f not in reintegres:
            fiche["demandes"] = []
        elif fiche["categorie"] not in CATEGORIES_ECARTEES and not fiche["demandes"]:
            alertes.append(f"{id_f} est actionnable mais sans demande extraite.")
    return fiches, alertes


def est_ecarte(fiche: dict, reintegres: set[str]) -> bool:
    if fiche["id"] in reintegres and fiche["demandes"]:
        return False
    return fiche["categorie"] in CATEGORIES_ECARTEES or not fiche["demandes"]


def indexer_demandes(fiches: dict[str, dict], reintegres: set[str]) -> dict[str, dict]:
    """Demandes des feedbacks non écartés, identifiées « FB-xxx#n »."""
    demandes = {}
    for id_f, fiche in fiches.items():
        if est_ecarte(fiche, reintegres):
            continue
        for n, d in enumerate(fiche["demandes"], start=1):
            demandes[f"{id_f}#{n}"] = {**d, "feedback_id": id_f}
    return demandes
