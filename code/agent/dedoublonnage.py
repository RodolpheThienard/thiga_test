"""R4 – Une demande par personne et par problème, et statistiques d'un thème."""
from __future__ import annotations

from collections import defaultdict

from .config import ENJEUX, GRAVITES


def identite(feedback: dict) -> str:
    """Identifie le demandeur : adresse email, sinon nom d'auteur (avis Play Store), sinon l'identifiant."""
    if feedback.get("email"):
        return feedback["email"].strip().lower()
    if feedback.get("auteur"):
        return "auteur:" + feedback["auteur"].strip().lower()
    return "id:" + feedback["id"]


def gravite_max(gravites: list[str]) -> str | None:
    valides = [g for g in gravites if g in GRAVITES]
    return max(valides, key=GRAVITES.index) if valides else None


def enjeu_max(enjeux: list[str]) -> str | None:
    valides = [e for e in enjeux if e in ENJEUX]
    return max(valides, key=ENJEUX.index) if valides else None


def statistiques_theme(ids_demandes: list[str], demandes: dict[str, dict], feedbacks: dict[str, dict]) -> dict:
    """Calcule volume, demandeurs distincts, relances, gravité et enjeux d'un thème.

    `demandes` : id_demande -> {"feedback_id", "gravite", "enjeu_business", ...}
    `feedbacks` : id -> feedback
    """
    par_demandeur: dict[str, list[dict]] = defaultdict(list)
    ids_feedbacks = []
    for id_d in ids_demandes:
        d = demandes[id_d]
        fb = feedbacks[d["feedback_id"]]
        if fb["id"] not in ids_feedbacks:
            ids_feedbacks.append(fb["id"])
        par_demandeur[identite(fb)].append({**d, "date": fb["date"], "auteur": fb.get("auteur")})

    demandeurs = []
    for ident, liste in par_demandeur.items():
        demandeurs.append({
            "identite": ident,
            "auteur": liste[0]["auteur"],
            "nb_messages": len({x["feedback_id"] for x in liste}),
            "gravite": gravite_max([x["gravite"] for x in liste]),
            "enjeu_business": enjeu_max([x["enjeu_business"] for x in liste]),
        })

    toutes_gravites = [demandes[i]["gravite"] for i in ids_demandes]
    tous_enjeux = [demandes[i]["enjeu_business"] for i in ids_demandes]
    enjeux_presents = sorted(set(e for e in tous_enjeux if e in ENJEUX), key=ENJEUX.index, reverse=True)
    nb_messages = len(ids_feedbacks)
    return {
        "ids_feedbacks": ids_feedbacks,
        "nb_messages": nb_messages,
        "nb_demandeurs": len(demandeurs),
        "nb_relances": nb_messages - len(demandeurs),
        "demandeurs": demandeurs,
        "gravite_max": gravite_max(toutes_gravites),
        "enjeux": enjeux_presents,
        "enjeu_max": enjeu_max(tous_enjeux),
        "dates": sorted(feedbacks[i]["date"] for i in ids_feedbacks),
    }
