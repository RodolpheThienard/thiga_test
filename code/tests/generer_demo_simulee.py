"""Produit cache/demo_simulee.json : une analyse SIMULÉE (faux modèle répondant à partir des étiquettes).

Elle sert uniquement à explorer l'interface sans clé API. Elle est signalée comme simulée dans l'interface
et ne doit pas servir à évaluer l'agent. Usage : python -m tests.generer_demo_simulee
"""
import tempfile

from agent import pipeline
from agent.config import DOSSIER_CACHE, FICHIER_FEEDBACKS, Parametres
from agent.llm import ClientLLM
from agent.sources import charger_fichier
from tests.faux_llm import faux_transport

if __name__ == "__main__":
    client = ClientLLM(transport=faux_transport, dossier_cache=tempfile.mkdtemp())
    sortie = DOSSIER_CACHE / "demo_simulee.json"
    pipeline.sauvegarder = (lambda f: (lambda a, chemin=sortie: f(a, chemin)))(pipeline.sauvegarder)
    analyse = pipeline.analyser(charger_fichier(FICHIER_FEEDBACKS), client, Parametres())
    analyse["meta"]["simulee"] = True
    analyse["meta"]["modele"] = "simulation (aucun appel au modèle)"
    pipeline.sauvegarder(analyse)
    print("Analyse simulée écrite dans", sortie)
