"""Schémas des sorties du LLM (validés avec pydantic) et du format commun des feedbacks."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Categorie = Literal["Bug", "Demande de fonctionnalité", "UX/Utilisabilité", "Question/Support", "Non actionnable"]
Gravite = Literal["Bloquant", "Majeur", "Mineur", "Cosmétique"]
Enjeu = Literal["Rétention", "Adoption", "Expansion", "Efficacité"]


class Feedback(BaseModel):
    """Format commun aux deux sources (fichier JSON et Gmail)."""

    id: str
    canal: str
    source: str
    date: str  # ISO 8601
    auteur: Optional[str] = None
    email: Optional[str] = None
    entreprise: Optional[str] = None
    objet: Optional[str] = None
    contenu: str


# --- P1 ---
class DemandeLLM(BaseModel):
    probleme: str
    gravite: Gravite
    enjeu_business: Enjeu
    hors_vision: bool = False


class FicheLLM(BaseModel):
    id: str
    categorie: Categorie
    demandes: list[DemandeLLM] = Field(default_factory=list)
    justification: str = ""


class ReponseP1(BaseModel):
    fiches: list[FicheLLM]


# --- P2 ---
class ThemeLLM(BaseModel):
    titre: str
    description: str = ""
    demandes: list[str]
    backlog_id: Optional[str] = None
    couverture_backlog: Optional[str] = None
    hors_vision: bool = False
    justification: str = ""


class ReponseP2(BaseModel):
    themes: list[ThemeLLM]


# --- P3 ---
class EstimationLLM(BaseModel):
    theme_id: str
    impact: float
    justification_impact: str = ""
    confidence: int
    justification_confidence: str = ""
    effort: int
    justification_effort: str = ""
    hypotheses_effort: str = ""


class ReponseP3(BaseModel):
    estimations: list[EstimationLLM]


# --- P4 ---
class JustificationLLM(BaseModel):
    theme_id: str
    justification: str
    point_attention: str = ""


class ReponseP4(BaseModel):
    justifications: list[JustificationLLM]


# --- P5 ---
class CritereLLM(BaseModel):
    scenario: str
    gherkin: str


class UserStoryLLM(BaseModel):
    titre: str
    story: str
    criteres_acceptation: list[CritereLLM]
    story_points: int
    hypotheses_estimation: str = ""
    ecart_avec_effort_rice: str = ""
    decoupage: list[str] = Field(default_factory=list)
    questions_ouvertes: list[str] = Field(default_factory=list)
    hors_perimetre: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
