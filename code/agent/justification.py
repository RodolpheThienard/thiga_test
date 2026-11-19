"""P3 (estimation) et P4 (justification du classement)."""
from __future__ import annotations

import json

from .schemas import ReponseP3, ReponseP4


def estimer(client, contexte: str, themes: list[dict]) -> dict[str, dict]:
    """themes : dicts préparés par le pipeline (stats, tendance, impact de base, extraits)."""
    if not themes:
        return {}
    message = "Thèmes à estimer :\n" + json.dumps(themes, ensure_ascii=False, indent=1)
    reponse = client.appeler("P3_estimation", contexte, message, ReponseP3, temperature=0)
    return {e.theme_id: e.model_dump() for e in reponse.estimations}


def justifier(client, contexte: str, classement: list[dict], capacite: int, points_must: int) -> dict[str, dict]:
    if not classement:
        return {}
    message = (
        f"Capacité du sprint : {capacite} points. Points engagés en Must : {points_must}.\n"
        "Classement calculé :\n" + json.dumps(classement, ensure_ascii=False, indent=1)
    )
    reponse = client.appeler("P4_justification", contexte, message, ReponseP4, temperature=0.3)
    return {j.theme_id: j.model_dump() for j in reponse.justifications}
