"""P5 – Rédaction des User Stories et export JSON (R8)."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .config import DOSSIER_EXPORTS
from .schemas import UserStoryLLM


def rediger(client, contexte: str, theme: dict, feedbacks: list[dict], backlog_element: dict | None,
            effort: int) -> dict:
    lignes = [{"id": f["id"], "canal": f["canal"], "contenu": f["contenu"]} for f in feedbacks]
    element = "aucun"
    if backlog_element:
        element = f"{backlog_element['id']} – {backlog_element['titre']} ({backlog_element['statut']}) : {backlog_element['description']}"
    message = (
        f"Thème : {theme['titre']} – {theme.get('description', '')}\n"
        f"Élément du backlog associé : {element}\n"
        f"Gravité maximale : {theme.get('gravite_max')} · Enjeux : {', '.join(theme.get('enjeux') or [])} · "
        f"Effort estimé (RICE) : {effort} points\n"
        "Feedbacks d'origine :\n" + json.dumps(lignes, ensure_ascii=False, indent=1)
    )
    return client.appeler("P5_user_story", contexte, message, UserStoryLLM, temperature=0.3).model_dump()


def exporter(stories: list[dict], dossier: Path = DOSSIER_EXPORTS) -> tuple[str, Path]:
    """Écrit l'export JSON et renvoie (contenu, chemin)."""
    horodatage = datetime.now()
    export = {
        "date_export": horodatage.isoformat(timespec="seconds"),
        "produit": "Orbiteam",
        "user_stories": [{"id": f"US-{i:03d}", **s} for i, s in enumerate(stories, start=1)],
    }
    contenu = json.dumps(export, ensure_ascii=False, indent=2)
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / f"user_stories_{horodatage:%Y%m%d_%H%M%S}.json"
    chemin.write_text(contenu, encoding="utf-8")
    return contenu, chemin
