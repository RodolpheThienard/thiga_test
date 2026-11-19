"""R6 – Score RICE : contrôles des estimations du LLM et calcul pondéré."""
from __future__ import annotations

from .config import BAREME_IMPACT, CONFIDENCES, ECHELLE_IMPACT, FIBONACCI


def impact_base(gravite: str | None) -> float:
    """Base fixe de l'Impact, déduite de la gravité la plus élevée du thème."""
    return BAREME_IMPACT.get(gravite or "", 1.0)


def _plus_proche(valeur: float, echelle: list) -> float:
    return min(echelle, key=lambda v: (abs(v - valeur), v))


def controler_impact(base: float, propose: float) -> tuple[float, str | None]:
    """L'Impact proposé doit être sur l'échelle et à un cran maximum de la base."""
    if propose not in ECHELLE_IMPACT:
        return base, f"Impact {propose} hors échelle : ramené à la base ({base})."
    ecart = abs(ECHELLE_IMPACT.index(propose) - ECHELLE_IMPACT.index(base))
    if ecart > 1:
        return base, f"Impact {propose} trop éloigné de la base ({base}) : ramené à la base."
    return propose, None


def controler_confidence(valeur: int) -> tuple[int, str | None]:
    if valeur in CONFIDENCES:
        return valeur, None
    corrigee = int(_plus_proche(valeur, CONFIDENCES))
    return corrigee, f"Confidence {valeur} hors échelle : ramenée à {corrigee}."


def controler_effort(valeur: int, estimation_backlog: int | None = None) -> tuple[int, str | None]:
    if estimation_backlog:
        if valeur != estimation_backlog:
            return estimation_backlog, f"Estimation du backlog reprise ({estimation_backlog} points)."
        return valeur, None
    if valeur in FIBONACCI:
        return valeur, None
    corrigee = int(_plus_proche(valeur, FIBONACCI))
    return corrigee, f"Effort {valeur} hors suite de Fibonacci : ramené à {corrigee}."


def score_rice(reach: float, impact: float, confidence_pct: float, effort: float,
               poids_reach: float = 1.0, poids_impact: float = 1.0,
               poids_confidence: float = 1.0, poids_effort: float = 1.0) -> float:
    """Score = Reach^p1 × Impact^p2 × Confidence^p3 / Effort^p4 (tous poids à 1 = RICE classique)."""
    if effort <= 0:
        raise ValueError("L'effort doit être strictement positif.")
    confidence = confidence_pct / 100
    return (reach ** poids_reach) * (impact ** poids_impact) * (confidence ** poids_confidence) / (effort ** poids_effort)
