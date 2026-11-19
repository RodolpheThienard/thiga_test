"""Appels au LLM : chargement des prompts, validation JSON, relance unique, cache (R2)."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Callable, Type, TypeVar

from pydantic import BaseModel, ValidationError

from .config import DOSSIER_CACHE_APPELS, DOSSIER_PROMPTS, MODELE

T = TypeVar("T", bound=BaseModel)

# transport(systeme, messages, temperature) -> texte de la réponse
Transport = Callable[[str, list[dict], float], str]


class ErreurLLM(RuntimeError):
    """Réponse du modèle inexploitable après une relance."""


class ErreurHorsLigne(RuntimeError):
    """Appel demandé en mode hors ligne alors que la réponse n'est pas en cache."""


def charger_prompt(nom: str, contexte: str) -> str:
    texte = (DOSSIER_PROMPTS / f"{nom}.txt").read_text(encoding="utf-8")
    return texte.replace("{contexte_produit}", contexte)


def extraire_json(texte: str) -> str:
    """Isole l'objet JSON d'une réponse (tolère un bloc ```json ou du texte autour)."""
    bloc = re.search(r"```(?:json)?\s*(\{.*\})\s*```", texte, re.S)
    if bloc:
        return bloc.group(1)
    debut, fin = texte.find("{"), texte.rfind("}")
    if debut == -1 or fin <= debut:
        raise ValueError("Aucun objet JSON dans la réponse.")
    return texte[debut:fin + 1]


def transport_anthropic(cle_api: str, modele: str = MODELE, max_tokens: int = 16000) -> Transport:
    import anthropic

    client = anthropic.Anthropic(api_key=cle_api, max_retries=2, timeout=300)

    def appeler(systeme: str, messages: list[dict], temperature: float) -> str:
        # Les modèles récents n'exposent plus le réglage de température : il n'est pas transmis.
        # La reproductibilité est assurée par le cache (une même entrée renvoie la même réponse).
        reponse = client.messages.create(model=modele, max_tokens=max_tokens, system=systeme, messages=messages)
        return "".join(b.text for b in reponse.content if getattr(b, "type", "") == "text")

    return appeler


class ClientLLM:
    """Point d'entrée unique vers le modèle.

    - hors_ligne=True : seules les réponses en cache sont utilisables (aucun appel réseau).
    - transport : fonction d'appel au modèle (remplaçable par un faux transport dans les tests).
    """

    def __init__(self, transport: Transport | None = None, hors_ligne: bool = False,
                 dossier_cache: Path = DOSSIER_CACHE_APPELS, modele: str = MODELE):
        self.transport = transport
        self.hors_ligne = hors_ligne or transport is None
        self.dossier_cache = Path(dossier_cache)
        self.modele = modele
        self.nb_appels_reels = 0
        self.nb_depuis_cache = 0

    def _cle(self, systeme: str, message: str, temperature: float) -> str:
        brut = json.dumps([self.modele, systeme, message, temperature], ensure_ascii=False)
        return hashlib.sha256(brut.encode("utf-8")).hexdigest()[:32]

    def appeler(self, nom_prompt: str, contexte: str, message: str, schema: Type[T], temperature: float = 0) -> T:
        systeme = charger_prompt(nom_prompt, contexte)
        cle = self._cle(systeme, message, temperature)
        fichier = self.dossier_cache / f"{nom_prompt}_{cle}.json"

        if fichier.exists():
            self.nb_depuis_cache += 1
            return schema.model_validate_json(json.loads(fichier.read_text(encoding="utf-8"))["reponse"])
        if self.hors_ligne:
            raise ErreurHorsLigne(
                f"Réponse absente du cache pour {nom_prompt} : lancez d'abord une analyse en mode connecté."
            )

        messages = [{"role": "user", "content": message}]
        texte = self.transport(systeme, messages, temperature)
        self.nb_appels_reels += 1
        try:
            objet = schema.model_validate_json(extraire_json(texte))
        except (ValueError, ValidationError) as erreur:
            # Relance unique : on renvoie au modèle l'erreur de validation.
            messages += [
                {"role": "assistant", "content": texte},
                {"role": "user", "content": (
                    "Ta réponse n'est pas exploitable : " + str(erreur)[:1500]
                    + "\nRenvoie uniquement le JSON corrigé, conforme au schéma demandé, sans aucun texte autour."
                )},
            ]
            texte = self.transport(systeme, messages, temperature)
            self.nb_appels_reels += 1
            try:
                objet = schema.model_validate_json(extraire_json(texte))
            except (ValueError, ValidationError) as erreur2:
                raise ErreurLLM(f"{nom_prompt} : réponse invalide après relance ({str(erreur2)[:300]}).") from erreur2

        self.dossier_cache.mkdir(parents=True, exist_ok=True)
        fichier.write_text(json.dumps({"prompt": nom_prompt, "reponse": objet.model_dump_json()}, ensure_ascii=False), encoding="utf-8")
        return objet
