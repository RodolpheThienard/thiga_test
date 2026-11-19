"""Faux transport LLM pour les tests : répond à partir des étiquettes de référence, sans réseau."""
import json
import re
from agent.config import FICHIER_LABELS

LABELS = json.loads(FICHIER_LABELS.read_text(encoding="utf-8"))
PAR_ID = {l["id"]: l for l in LABELS["feedbacks"]}


def faux_transport(systeme, messages, temperature):
    dernier = messages[-1]["content"]
    if "qualifier des feedbacks" in systeme:
        ids = re.findall(r'"id": "(FB-\d+)"', dernier)
        fiches = []
        for i in ids:
            l = PAR_ID[i]
            demandes = [{"probleme": f"Problème {t}", "gravite": l["gravite"], "enjeu_business": l["enjeu_business"],
                         "hors_vision": t == "HV"} for t in l["themes"]]
            fiches.append({"id": i, "categorie": l["categorie"], "demandes": demandes, "justification": "test"})
        return json.dumps({"fiches": fiches}, ensure_ascii=False)
    if "regrouper les demandes" in systeme:
        ids = re.findall(r'"id_demande": "(FB-\d+#\d+)"', dernier)
        groupes = {}
        for d in ids:
            fb, n = d.split("#")
            t = PAR_ID[fb]["themes"][int(n) - 1]
            groupes.setdefault(t, []).append(d)
        themes = [{"titre": LABELS["themes"][t]["libelle"], "description": "", "demandes": ds,
                   "backlog_id": LABELS["themes"][t]["backlog_attendu"] if LABELS["themes"][t]["backlog_attendu"].startswith("BL-1") and "insuffisant" not in LABELS["themes"][t]["backlog_attendu"] else None,
                   "couverture_backlog": None, "hors_vision": t == "HV", "justification": "test"} for t, ds in groupes.items()]
        return json.dumps({"themes": themes}, ensure_ascii=False)
    if "trois estimations" in systeme:
        themes = json.loads(dernier.split("\n", 1)[1])
        return json.dumps({"estimations": [{"theme_id": t["theme_id"], "impact": t["impact_base"], "confidence": 80,
                                            "effort": t["estimation_backlog"] or 5} for t in themes]})
    if "classement MoSCoW ci-dessous" in systeme:
        ids = re.findall(r'"theme_id": "(TH-\d+)"', dernier)
        return json.dumps({"justifications": [{"theme_id": i, "justification": "test"} for i in ids]})
    if "User Story prête" in systeme:
        return json.dumps({"titre": "US test", "story": "En tant que PO, je veux…, afin de…",
                           "criteres_acceptation": [{"scenario": "Nominal", "gherkin": "Étant donné…\nQuand…\nAlors…"}],
                           "story_points": 5, "sources": ["FB-003"]}, ensure_ascii=False)
    raise AssertionError("Prompt inconnu")
