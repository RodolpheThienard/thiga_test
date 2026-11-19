"""R5 – Tendance d'un thème : période en cours comparée à la période précédente.

La période en cours couvre les `periode_jours` jours qui se terminent à la date de référence incluse.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

NOUVEAU, HAUSSE, BAISSE, STABLE = "Nouveau", "En hausse", "En baisse", "Stable"
SYMBOLES = {NOUVEAU: "🆕", HAUSSE: "↗", BAISSE: "↘", STABLE: "→"}


def _en_date(valeur: str | datetime | date) -> date:
    if isinstance(valeur, datetime):
        return valeur.date()
    if isinstance(valeur, date):
        return valeur
    return datetime.fromisoformat(valeur).date()


def calculer_tendance(dates: list, date_reference: date, periode_jours: int = 7, seuil: int = 2) -> dict:
    debut_courant = date_reference - timedelta(days=periode_jours - 1)
    debut_precedent = debut_courant - timedelta(days=periode_jours)
    jours = [_en_date(d) for d in dates]
    courant = sum(debut_courant <= j <= date_reference for j in jours)
    precedent = sum(debut_precedent <= j < debut_courant for j in jours)
    anterieurs = sum(j < debut_courant for j in jours)

    if courant > 0 and anterieurs == 0:
        statut = NOUVEAU
    elif courant - precedent >= seuil:
        statut = HAUSSE
    elif precedent - courant >= seuil:
        statut = BAISSE
    else:
        statut = STABLE
    return {
        "statut": statut,
        "courant": courant,
        "precedent": precedent,
        "periode": f"{debut_courant:%d/%m} → {date_reference:%d/%m}",
        "periode_precedente": f"{debut_precedent:%d/%m} → {debut_courant - timedelta(days=1):%d/%m}",
    }
