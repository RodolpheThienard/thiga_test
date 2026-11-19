"""Suivi des problèmes par le PO : état affiché et information des demandeurs par email.

Tout est déterministe : aucun appel au modèle. L'envoi n'a lieu que sur action explicite du PO.
"""
from __future__ import annotations

import json
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Callable

from .config import FICHIER_SUIVI

# Sources dont les adresses sont réelles. Les adresses du jeu de démonstration sont fictives :
# on ne leur écrit jamais.
SOURCES_REELLES = {"Boîte Gmail", "JIRA"}

EN_COURS, DEPLOYE = "En cours de traitement", "Correctif déployé"

# État affiché dans l'onglet Analyser, du plus urgent au plus avancé.
A_CREER = "À créer"
ETATS = [A_CREER, "Livré, insuffisant", "Ticket créé", "En cours (backlog)", EN_COURS, DEPLOYE]


def cle_suivi(ligne: dict) -> str:
    """Clé stable d'un problème d'une analyse à l'autre : l'élément du backlog, à défaut le titre."""
    return ligne.get("backlog_id") or ligne["titre"]


def etat_theme(statut_backlog: str | None, couverture: str | None, suivi: dict | None = None) -> str:
    """État d'un problème : le suivi du PO prime, sinon on lit le backlog.

    - aucun élément du backlog : « À créer » (demande l'attention du PO) ;
    - élément livré mais ne couvrant qu'une partie du besoin : « Livré, insuffisant » ;
    - élément « À faire » : « Ticket créé » ; élément « En cours » : « En cours (backlog) ».
    """
    if suivi and suivi.get("statut") in (EN_COURS, DEPLOYE):
        return suivi["statut"]
    if not statut_backlog:
        return A_CREER
    if statut_backlog == "Livré":
        return "Livré, insuffisant" if couverture == "partielle" else DEPLOYE
    if statut_backlog == "En cours":
        return "En cours (backlog)"
    return "Ticket créé"


def destinataires(ids_feedbacks: list[str], feedbacks: dict[str, dict]) -> tuple[list[str], int]:
    """Adresses distinctes des demandeurs venant d'une source réelle, et nombre de demandeurs exclus (démo)."""
    reelles, fictives = [], set()
    for i in ids_feedbacks:
        fb = feedbacks[i]
        adresse = (fb.get("email") or "").strip().lower()
        if not adresse or "@" not in adresse:
            continue
        if fb.get("source") in SOURCES_REELLES:
            if adresse not in reelles:
                reelles.append(adresse)
        else:
            fictives.add(adresse)
    return reelles, len(fictives - set(reelles))


def rediger_email(type_message: str, titre: str, produit: str = "Orbiteam") -> tuple[str, str]:
    """Modèle d'email (objet, corps), modifiable par le PO avant l'envoi."""
    if type_message == DEPLOYE:
        objet = f"{produit} – Correctif déployé : {titre}"
        corps = (f"Bonjour,\n\nVous nous aviez signalé le problème suivant : « {titre} ».\n\n"
                 "Un correctif vient d'être déployé. Pouvez-vous nous confirmer que tout fonctionne de votre côté ? "
                 "Il vous suffit de répondre à cet email.\n\n"
                 f"Merci pour votre retour, qui nous a aidés à améliorer {produit}.\n\nL'équipe produit {produit}")
    else:
        objet = f"{produit} – Votre signalement est en cours de traitement : {titre}"
        corps = (f"Bonjour,\n\nVous nous avez signalé le problème suivant : « {titre} ».\n\n"
                 "Plusieurs utilisateurs nous ont remonté le même sujet. Il a été priorisé et notre équipe "
                 "y travaille. Nous vous écrirons dès que le correctif sera déployé.\n\n"
                 f"Merci pour votre retour.\n\nL'équipe produit {produit}")
    return objet, corps


def envoyer_email(expediteur: str, mot_de_passe: str, adresses: list[str], objet: str, corps: str,
                  smtp: Callable[..., smtplib.SMTP_SSL] = smtplib.SMTP_SSL) -> None:
    """Envoie un seul email : le PO en destinataire, les demandeurs en copie cachée (adresses non exposées)."""
    if not adresses:
        raise ValueError("Aucun destinataire.")
    message = EmailMessage()
    message["From"] = expediteur
    message["To"] = expediteur
    message["Subject"] = objet
    message.set_content(corps)
    with smtp("smtp.gmail.com", 465, timeout=30) as serveur:
        serveur.login(expediteur, mot_de_passe)
        serveur.send_message(message, from_addr=expediteur, to_addrs=[expediteur, *adresses])


def charger_suivi(chemin: Path = FICHIER_SUIVI) -> dict:
    try:
        return json.loads(Path(chemin).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def enregistrer_envoi(cle: str, statut: str, nb_destinataires: int, chemin: Path = FICHIER_SUIVI) -> dict:
    """Mémorise le dernier envoi d'un problème (pas les adresses : seulement leur nombre)."""
    suivi = charger_suivi(chemin)
    historique = suivi.get(cle, {}).get("historique", [])
    envoi = {"statut": statut, "date": datetime.now().strftime("%Y-%m-%dT%H:%M"), "nb_destinataires": nb_destinataires}
    suivi[cle] = {**envoi, "historique": historique + [envoi]}
    Path(chemin).parent.mkdir(parents=True, exist_ok=True)
    Path(chemin).write_text(json.dumps(suivi, ensure_ascii=False, indent=1), encoding="utf-8")
    return suivi
