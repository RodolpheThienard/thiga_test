"""Paramètres par défaut de l'agent et lecture de la configuration locale (.env).

Les valeurs ci-dessous traduisent les règles de gestion R1 à R9 de la documentation.
Aucun secret n'est écrit ici : ils sont lus depuis le fichier .env.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field, asdict
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_DATA = RACINE / "data"
DOSSIER_PROMPTS = RACINE / "prompts"
DOSSIER_CACHE = RACINE / "cache"
DOSSIER_CACHE_APPELS = DOSSIER_CACHE / "appels"
FICHIER_DERNIERE_ANALYSE = DOSSIER_CACHE / "derniere_analyse.json"
FICHIER_SUIVI = DOSSIER_CACHE / "suivi_po.json"  # emails envoyés par le PO aux demandeurs
DOSSIER_EXPORTS = RACINE / "exports"

FICHIER_FEEDBACKS = DOSSIER_DATA / "feedbacks.json"
FICHIER_BACKLOG = DOSSIER_DATA / "backlog.json"
FICHIER_CONTEXTE = DOSSIER_DATA / "contexte_produit.md"
FICHIER_LABELS = DOSSIER_DATA / "labels_attendus.json"

MODELE = "claude-sonnet-5-5"

# --- Référentiels métier (section 2.1 et 2.5 de la documentation) ---
CATEGORIES = ["Bug", "Demande de fonctionnalité", "UX/Utilisabilité", "Question/Support", "Non actionnable"]
CATEGORIES_ECARTEES = {"Question/Support", "Non actionnable"}  # R3
GRAVITES = ["Cosmétique", "Mineur", "Majeur", "Bloquant"]  # ordre croissant
ENJEUX = ["Efficacité", "Expansion", "Adoption", "Rétention"]  # ordre croissant de criticité
BAREME_IMPACT = {"Bloquant": 3.0, "Majeur": 2.0, "Mineur": 1.0, "Cosmétique": 0.5}  # R6, barème fixe
ECHELLE_IMPACT = [0.25, 0.5, 1.0, 2.0, 3.0]
CONFIDENCES = [50, 80, 100]
FIBONACCI = [1, 2, 3, 5, 8, 13, 21, 34]
CATEGORIES_MOSCOW = ["Must", "Should", "Could", "Won't"]

# Date de référence du jeu de démonstration : dernier jour inclus de la période en cours (R5).
DATE_REFERENCE_DEMO = date(2026, 11, 16)

TAILLE_LOT_P1 = 10

# R1 – Tickets JIRA lus par défaut : ceux créés sur les 30 derniers jours.
JQL_PAR_DEFAUT = "created >= -30d ORDER BY created DESC"


@dataclass
class Parametres:
    """Réglages modifiables par le PO dans l'interface."""

    periode_jours: int = 7  # R5
    seuil_tendance: int = 2  # R5
    date_reference: date = DATE_REFERENCE_DEMO  # R5
    poids_reach: float = 1.0  # R6
    poids_impact: float = 1.0
    poids_confidence: float = 1.0
    poids_effort: float = 1.0
    capacite_sprint: int = 35  # R7
    regle_bloquant_retention: bool = True  # R7
    horizon_should_sprints: int = 1  # R7

    def signature_classement(self) -> dict:
        """Paramètres qui influencent le classement (sert à savoir si P4 est à jour)."""
        d = asdict(self)
        d["date_reference"] = self.date_reference.isoformat()
        return d


@dataclass
class ConfigLocale:
    cle_api: str | None = None
    gmail_adresse: str | None = None
    gmail_mot_de_passe: str | None = None
    gmail_dossier: str = "INBOX"
    jira_url: str | None = None
    jira_email: str | None = None
    jira_jeton: str | None = None
    jira_jql: str = JQL_PAR_DEFAUT


def lire_config_locale() -> ConfigLocale:
    load_dotenv(RACINE / ".env")
    return ConfigLocale(
        cle_api=os.getenv("ANTHROPIC_API_KEY") or None,
        gmail_adresse=os.getenv("GMAIL_ADRESSE") or None,
        gmail_mot_de_passe=os.getenv("GMAIL_APP_PASSWORD") or None,
        gmail_dossier=os.getenv("GMAIL_DOSSIER") or "INBOX",
        jira_url=os.getenv("JIRA_URL") or None,
        jira_email=os.getenv("JIRA_EMAIL") or None,
        jira_jeton=os.getenv("JIRA_API_TOKEN") or None,
        jira_jql=os.getenv("JIRA_JQL") or JQL_PAR_DEFAUT,
    )
