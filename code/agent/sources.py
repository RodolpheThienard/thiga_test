"""Lecture des feedbacks (R1) : fichier de sauvegarde multicanal, boîte Gmail et tickets JIRA."""
from __future__ import annotations

import email
import base64
import imaplib
import json
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from email.header import decode_header, make_header
from email.utils import parseaddr, parsedate_to_datetime
from html import unescape
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .schemas import Feedback


def charger_fichier(chemin: Path) -> list[dict]:
    """Charge le fichier de sauvegarde ; canal et date d'origine sont conservés."""
    donnees = json.loads(Path(chemin).read_text(encoding="utf-8"))
    return [Feedback(**f).model_dump() for f in donnees]


def _decoder(valeur: str | None) -> str:
    if not valeur:
        return ""
    try:
        return str(make_header(decode_header(valeur)))
    except Exception:
        return valeur


def _html_vers_texte(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    html = re.sub(r"(?i)<br\s*/?>|</p>|</div>", "\n", html)
    texte = unescape(re.sub(r"<[^>]+>", " ", html))
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", texte)).strip()


def _corps(message: email.message.Message) -> str:
    texte, html = None, None
    parties = message.walk() if message.is_multipart() else [message]
    for partie in parties:
        if partie.get_content_maintype() == "multipart" or partie.get("Content-Disposition", "").startswith("attachment"):
            continue
        charge = partie.get_payload(decode=True)
        if charge is None:
            continue
        contenu = charge.decode(partie.get_content_charset() or "utf-8", errors="replace")
        if partie.get_content_type() == "text/plain" and texte is None:
            texte = contenu
        elif partie.get_content_type() == "text/html" and html is None:
            html = contenu
    if texte and texte.strip():
        return texte.strip()
    return _html_vers_texte(html) if html else ""


def analyser_email(brut: bytes, uid: str) -> dict:
    """Transforme un email brut en feedback au format commun (canal « email »)."""
    message = email.message_from_bytes(brut)
    nom, adresse = parseaddr(_decoder(message.get("From")))
    try:
        date = parsedate_to_datetime(message.get("Date"))
        if date.tzinfo is not None:
            date = date.astimezone().replace(tzinfo=None)
    except Exception:
        date = datetime.now()
    domaine = adresse.split("@")[-1] if "@" in adresse else None
    return Feedback(
        id=f"MAIL-{uid}",
        canal="email",
        source="Boîte Gmail",
        date=date.strftime("%Y-%m-%dT%H:%M"),
        auteur=nom or adresse or "Inconnu",
        email=adresse.lower() or None,
        entreprise=domaine,
        objet=_decoder(message.get("Subject")) or None,
        contenu=_corps(message) or "(message vide)",
    ).model_dump()


def lire_gmail(adresse: str, mot_de_passe: str, dossier: str = "INBOX", jours: int = 30) -> list[dict]:
    """Lit les emails des N derniers jours dans le dossier indiqué (IMAP SSL)."""
    depuis = (datetime.now(timezone.utc) - timedelta(days=jours)).strftime("%d-%b-%Y")
    with imaplib.IMAP4_SSL("imap.gmail.com", 993, timeout=30) as imap:
        imap.login(adresse, mot_de_passe)
        statut, _ = imap.select(f'"{dossier}"', readonly=True)
        if statut != "OK":
            raise RuntimeError(f"Dossier Gmail introuvable : {dossier}")
        _, donnees = imap.uid("search", None, f"(SINCE {depuis})")
        feedbacks = []
        for uid in (donnees[0] or b"").split():
            _, contenu = imap.uid("fetch", uid, "(RFC822)")
            if contenu and isinstance(contenu[0], tuple):
                feedbacks.append(analyser_email(contenu[0][1], uid.decode()))
        return feedbacks


# ---------------------------------------------------------------- JIRA Cloud (API REST v3)
CHAMPS_JIRA = "summary,description,reporter,created"


def _adf_vers_texte(noeud) -> str:
    """Convertit une description JIRA (Atlassian Document Format) en texte brut."""
    if noeud is None:
        return ""
    if isinstance(noeud, str):  # description déjà en texte brut
        return noeud
    if isinstance(noeud, list):
        return "".join(_adf_vers_texte(n) for n in noeud)
    type_ = noeud.get("type")
    if type_ == "text":
        return noeud.get("text", "")
    if type_ == "hardBreak":
        return "\n"
    if type_ == "mention":
        return noeud.get("attrs", {}).get("text", "")
    texte = _adf_vers_texte(noeud.get("content", []))
    if type_ in ("paragraph", "heading", "codeBlock", "blockquote"):
        texte += "\n"
    return texte


def analyser_ticket_jira(ticket: dict) -> dict:
    """Transforme un ticket JIRA en feedback au format commun.

    Canal « ticket » : les tickets du jeu de démonstration tiennent la place des vrais tickets JIRA.
    Le demandeur est le rapporteur du ticket (email, à défaut nom affiché).
    """
    champs = ticket.get("fields", {})
    rapporteur = champs.get("reporter") or {}
    adresse = (rapporteur.get("emailAddress") or "").lower() or None
    try:
        date = datetime.strptime(champs["created"], "%Y-%m-%dT%H:%M:%S.%f%z").astimezone().replace(tzinfo=None)
    except (KeyError, TypeError, ValueError):
        date = datetime.now()
    description = re.sub(r"\n{3,}", "\n\n", _adf_vers_texte(champs.get("description"))).strip()
    resume = (champs.get("summary") or "").strip()
    return Feedback(
        id=f"JIRA-{ticket['key']}",
        canal="ticket",
        source="JIRA",
        date=date.strftime("%Y-%m-%dT%H:%M"),
        auteur=rapporteur.get("displayName") or adresse or "Inconnu",
        email=adresse,
        entreprise=adresse.split("@")[-1] if adresse else None,
        objet=resume or None,
        contenu=description or resume or "(ticket vide)",
    ).model_dump()


def _requete_http(url: str, entetes: dict) -> dict:
    try:
        with urlopen(Request(url, headers=entetes), timeout=30) as reponse:
            return json.loads(reponse.read().decode("utf-8"))
    except HTTPError as e:
        motifs = {400: "requête JQL invalide", 401: "email ou jeton API refusé", 403: "accès refusé au projet",
                  404: "adresse JIRA introuvable"}
        raise RuntimeError(f"JIRA a répondu {e.code} ({motifs.get(e.code, 'erreur')}).") from None
    except URLError as e:
        raise RuntimeError(f"JIRA injoignable ({e.reason}).") from None


def lire_jira(url: str, adresse: str, jeton: str, jql: str, max_tickets: int = 200,
              requete: Callable[[str, dict], dict] | None = None) -> list[dict]:
    """Lit les tickets JIRA Cloud qui répondent à la requête JQL (pagination par jeton)."""
    requete = requete or _requete_http
    identifiants = base64.b64encode(f"{adresse}:{jeton}".encode()).decode()
    entetes = {"Authorization": f"Basic {identifiants}", "Accept": "application/json"}
    base = f"{url.rstrip('/')}/rest/api/3/search/jql"
    tickets, jeton_page = [], None
    while len(tickets) < max_tickets:
        params = {"jql": jql, "fields": CHAMPS_JIRA, "maxResults": min(100, max_tickets - len(tickets))}
        if jeton_page:
            params["nextPageToken"] = jeton_page
        page = requete(f"{base}?{urlencode(params)}", entetes)
        tickets += [analyser_ticket_jira(t) for t in page.get("issues", [])]
        jeton_page = page.get("nextPageToken")
        if not jeton_page:
            break
    return tickets[:max_tickets]


def _normaliser(texte: str) -> str:
    """Minuscules et sans accents, pour une recherche tolérante (« Sécurité » = « securite »)."""
    decompose = unicodedata.normalize("NFKD", texte.casefold())
    return "".join(c for c in decompose if not unicodedata.combining(c))


def filtrer_par_mot_cle(feedbacks: list[dict], mot_cle: str | None) -> list[dict]:
    """Garde les emails dont l'objet ou le contenu contient le mot-clé (R1).

    Recherche insensible à la casse et aux accents. Un mot-clé vide ne filtre rien.
    """
    cle = _normaliser((mot_cle or "").strip())
    if not cle:
        return feedbacks
    return [f for f in feedbacks
            if cle in _normaliser(f"{f.get('objet') or ''} {f.get('contenu') or ''}")]


def fusionner(*listes: list[dict]) -> list[dict]:
    """Fusionne les sources, sans doublon d'identifiant, triées par date."""
    vus, resultat = set(), []
    for liste in listes:
        for f in liste:
            if f["id"] not in vus:
                vus.add(f["id"])
                resultat.append(f)
    return sorted(resultat, key=lambda f: f["date"])
