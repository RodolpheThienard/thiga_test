from datetime import date
import pytest
from agent import pipeline
from agent.config import FICHIER_FEEDBACKS, Parametres
from agent.llm import ClientLLM
from agent.sources import charger_fichier
from tests.faux_llm import faux_transport


@pytest.fixture
def analyse(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "FICHIER_DERNIERE_ANALYSE", tmp_path / "derniere.json")
    monkeypatch.setattr(pipeline, "sauvegarder", lambda a, chemin=tmp_path / "derniere.json": None)
    client = ClientLLM(transport=faux_transport, dossier_cache=tmp_path / "appels")
    return pipeline.analyser(charger_fichier(FICHIER_FEEDBACKS), client, Parametres()), client


def ligne(tableau, mot):
    return next(l for l in tableau["lignes"] if mot in l["titre"])


def test_bout_en_bout_filtrage_et_themes(analyse):
    a, _ = analyse
    assert len(a["ecartes"]) == 6  # 3 questions support + 3 non actionnables (spam, remerciements)
    assert len(a["themes"]) == 10  # 9 thèmes + hors vision


def test_tableau_dedoublonnage_tendance_moscow(analyse):
    a, _ = analyse
    t = pipeline.calculer_tableau(a, Parametres())
    sso, gitlab, notifs = ligne(t, "SSO"), ligne(t, "GitLab"), ligne(t, "notifications")
    assert (sso["nb_messages"], sso["nb_demandeurs"], sso["tendance"]["statut"]) == (8, 6, "Nouveau")
    assert (gitlab["nb_messages"], gitlab["nb_demandeurs"]) == (5, 2)
    assert notifs["tendance"]["statut"] == "En baisse"
    assert sso["moscow"] == "Must" and ligne(t, "hors vision")["moscow"] == "Won't"
    assert gitlab["effort"] == 13  # estimation du backlog reprise


def test_ajustement_du_po_recalcule_le_score(analyse):
    a, _ = analyse
    p = Parametres()
    avant = ligne(pipeline.calculer_tableau(a, p), "GitLab")
    apres = ligne(pipeline.calculer_tableau(a, p, {avant["theme_id"]: {"impact": 3, "moscow": "Must"}}), "GitLab")
    assert apres["score"] > avant["score"] and apres["moscow"] == "Must" and "impact" in apres["ajuste"]


def test_justifications_perimees_apres_modification(analyse):
    a, _ = analyse
    p = Parametres()
    assert pipeline.calculer_tableau(a, p)["justifications_a_jour"]
    assert not pipeline.calculer_tableau(a, Parametres(capacite_sprint=20))["justifications_a_jour"]


def test_user_stories_des_themes_coches(analyse):
    a, client = analyse
    t = pipeline.calculer_tableau(a, Parametres())
    cible = ligne(t, "PDF")["theme_id"]
    assert pipeline.generer_user_stories(a, client, [cible], Parametres(), {}) == []
    assert a["user_stories"][cible]["titre"] == "US test"
