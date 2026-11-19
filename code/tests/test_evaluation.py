from agent import pipeline
from agent.config import FICHIER_FEEDBACKS, Parametres
from agent.llm import ClientLLM
from agent.sources import charger_fichier
from evaluation.evaluer import evaluer
from tests.faux_llm import faux_transport


def test_agent_parfait_atteint_100_pourcent(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "sauvegarder", lambda *a, **k: None)
    client = ClientLLM(transport=faux_transport, dossier_cache=tmp_path)
    a = pipeline.analyser(charger_fichier(FICHIER_FEEDBACKS), client, Parametres())
    r = evaluer(a)
    assert all(m["taux"] == 1.0 for m in r["mesures"]), r["erreurs"]


def test_erreurs_detectees(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "sauvegarder", lambda *a, **k: None)
    client = ClientLLM(transport=faux_transport, dossier_cache=tmp_path)
    a = pipeline.analyser(charger_fichier(FICHIER_FEEDBACKS), client, Parametres())
    a["fiches"]["FB-019"]["categorie"] = "Bug"          # spam mal classé
    a["ecartes"].remove("FB-019")
    a["fiches"]["FB-003"]["demandes"][0]["gravite"] = "Bloquant"
    r = {m["mesure"]: m for m in evaluer(a)["mesures"]}
    assert not r["Spam et remerciements écartés"]["atteint"]
    assert r["Gravité"]["taux"] < 1
