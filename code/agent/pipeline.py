"""Enchaînement des étapes de l'agent.

Étapes avec LLM : classification (P1), regroupement (P2), estimation (P3), justification (P4), User Stories (P5).
Étapes en code : filtrage (R3), dédoublonnage (R4), tendances (R5), score RICE (R6), MoSCoW (R7).

`analyser` produit une « analyse » sérialisable (sauvegardée en cache pour le mode hors ligne).
`calculer_tableau` recalcule instantanément scores et classement à partir de l'analyse, des réglages
et des ajustements du PO, sans appel au modèle.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from . import classification, regroupement
from .config import FICHIER_BACKLOG, FICHIER_CONTEXTE, FICHIER_DERNIERE_ANALYSE, MODELE, Parametres
from .dedoublonnage import statistiques_theme
from .justification import estimer, justifier
from .moscow import repartir
from .rice import controler_confidence, controler_effort, controler_impact, impact_base, score_rice
from .tendances import calculer_tendance
from .user_stories import rediger


def charger_contexte() -> str:
    return FICHIER_CONTEXTE.read_text(encoding="utf-8")


def charger_backlog() -> list[dict]:
    return json.loads(FICHIER_BACKLOG.read_text(encoding="utf-8"))


def _estimation_backlog(theme: dict, backlog: dict[str, dict]) -> int | None:
    """L'estimation du backlog est reprise si l'élément couvre tout le besoin et n'est pas déjà livré."""
    element = backlog.get(theme.get("backlog_id") or "")
    if not element or element.get("statut") == "Livré" or (theme.get("couverture_backlog") or "complète") != "complète":
        return None
    return element.get("estimation_points")


def _stats(analyse: dict, theme: dict, params: Parametres) -> dict:
    s = statistiques_theme(theme["demandes"], analyse["demandes"], analyse["feedbacks_index"])
    s["tendance"] = calculer_tendance(s["dates"], params.date_reference, params.periode_jours, params.seuil_tendance)
    return s


def _signature(params: Parametres, ajustements: dict) -> str:
    sans_coches = {t: {k: v for k, v in a.items() if k != "rediger"} for t, a in (ajustements or {}).items()}
    sans_coches = {t: a for t, a in sans_coches.items() if a}
    return json.dumps([params.signature_classement(), sans_coches], sort_keys=True, ensure_ascii=False)


def analyser(feedbacks: list[dict], client, params: Parametres, reintegres: set[str] | None = None,
             progression=None) -> dict:
    reintegres = set(reintegres or set())
    contexte, backlog = charger_contexte(), charger_backlog()
    etape = progression or (lambda _m: None)
    analyse = {
        "meta": {
            "date_analyse": datetime.now().isoformat(timespec="seconds"),
            "modele": MODELE,
            "sources": sorted({f["source"] for f in feedbacks}),
            "nb_feedbacks": len(feedbacks),
            "date_reference": params.date_reference.isoformat(),
            "reintegres": sorted(reintegres),
        },
        "feedbacks": feedbacks,
        "feedbacks_index": {f["id"]: f for f in feedbacks},
        "alertes": [],
        "user_stories": {},
    }

    fiches, alertes = classification.classer(client, contexte, feedbacks, reintegres, etape)
    analyse["fiches"] = fiches
    analyse["alertes"] += alertes
    analyse["ecartes"] = [i for i, f in fiches.items() if classification.est_ecarte(f, reintegres)]
    analyse["demandes"] = classification.indexer_demandes(fiches, reintegres)

    etape("Regroupement des demandes en thèmes")
    themes, alertes = regroupement.regrouper(client, contexte, analyse["demandes"], analyse["feedbacks_index"], backlog)
    analyse["themes"] = themes
    analyse["alertes"] += alertes

    etape("Estimation RICE (Impact, Confidence, Effort)")
    index_backlog = {b["id"]: b for b in backlog}
    a_estimer = []
    for t in themes:
        if t["hors_vision"]:
            continue
        s = _stats(analyse, t, params)
        extraits = [{"id": i, "contenu": analyse["feedbacks_index"][i]["contenu"][:400]} for i in s["ids_feedbacks"][:8]]
        a_estimer.append({
            "theme_id": t["theme_id"], "titre": t["titre"], "description": t["description"],
            "nb_demandeurs": s["nb_demandeurs"], "nb_messages": s["nb_messages"],
            "gravite_max": s["gravite_max"], "enjeux": s["enjeux"], "tendance": s["tendance"]["statut"],
            "impact_base": impact_base(s["gravite_max"]),
            "estimation_backlog": _estimation_backlog(t, index_backlog),
            "extraits": extraits,
        })
    analyse["estimations"] = estimer(client, contexte, a_estimer)

    etape("Justification du classement")
    regenerer_justifications(analyse, client, params, {}, sauvegarder_cache=False)
    sauvegarder(analyse)
    return analyse


def calculer_tableau(analyse: dict, params: Parametres, ajustements: dict | None = None) -> dict:
    """Recalcule tout ce qui est déterministe : statistiques, tendance, RICE, MoSCoW."""
    ajustements = ajustements or {}
    index_backlog = {b["id"]: b for b in charger_backlog()}
    lignes, alertes = [], []
    for t in analyse["themes"]:
        s = _stats(analyse, t, params)
        aj = ajustements.get(t["theme_id"], {})
        base = impact_base(s["gravite_max"])
        ligne = {
            **{k: t.get(k) for k in ("theme_id", "titre", "description", "demandes", "backlog_id",
                                     "couverture_backlog", "hors_vision", "justification")},
            **{k: s[k] for k in ("ids_feedbacks", "nb_messages", "nb_demandeurs", "nb_relances", "demandeurs",
                                 "gravite_max", "enjeux", "enjeu_max", "tendance")},
            "backlog_titre": index_backlog.get(t.get("backlog_id") or "", {}).get("titre"),
            "backlog_statut": index_backlog.get(t.get("backlog_id") or "", {}).get("statut"),
            "impact_base": base, "controles": [], "rediger": bool(aj.get("rediger")),
        }
        if t["hors_vision"]:
            ligne.update(impact=None, impact_llm=None, confidence=None, effort=0, score=0.0, estimation={})
        else:
            e = analyse.get("estimations", {}).get(t["theme_id"])
            if e is None:
                alertes.append(f"{t['theme_id']} n'a pas été estimé par l'agent : valeurs prudentes par défaut.")
                e = {"impact": base, "confidence": 50, "effort": 8, "justification_impact": "", "justification_confidence": "",
                     "justification_effort": "Estimation absente : valeur par défaut.", "hypotheses_effort": ""}
            impact, c1 = controler_impact(base, float(e["impact"]))
            confidence, c2 = controler_confidence(int(e["confidence"]))
            effort, c3 = controler_effort(int(e["effort"]), _estimation_backlog(t, index_backlog))
            ligne["controles"] = [c for c in (c1, c2, c3) if c]
            ligne.update(impact_llm=float(e["impact"]), estimation=e)
            # Les ajustements du PO remplacent les valeurs proposées.
            impact = float(aj.get("impact", impact))
            confidence = int(aj.get("confidence", confidence))
            effort = int(aj.get("effort", effort))
            ligne.update(impact=impact, confidence=confidence, effort=effort, score=score_rice(
                s["nb_demandeurs"], impact, confidence, effort,
                params.poids_reach, params.poids_impact, params.poids_confidence, params.poids_effort))
        ligne["ajuste"] = {k for k in ("impact", "confidence", "effort", "moscow") if k in aj}
        ligne["force"] = aj.get("moscow")
        lignes.append(ligne)

    repartition = repartir(
        [{"theme_id": l["theme_id"], "score": l["score"], "effort": l["effort"], "gravite_max": l["gravite_max"],
          "enjeux": l["enjeux"], "hors_vision": l["hors_vision"], "force": l["force"]} for l in lignes],
        capacite=params.capacite_sprint, regle_bloquant_retention=params.regle_bloquant_retention,
        horizon_should_sprints=params.horizon_should_sprints)
    ordre = {"Must": 0, "Should": 1, "Could": 2, "Won't": 3}
    for l in lignes:
        c = repartition["categories"][l["theme_id"]]
        l["moscow"], l["regle_appliquee"] = c["categorie"], c["regle_appliquee"]
        l["justification_classement"] = analyse.get("justifications", {}).get(l["theme_id"], {})
    lignes.sort(key=lambda l: (ordre[l["moscow"]], -l["score"]))
    for rang, l in enumerate(lignes, start=1):
        l["rang"] = rang

    return {
        "lignes": lignes,
        "points_must": repartition["points_must"],
        "points_should": repartition["points_should"],
        "alertes": repartition["alertes"] + alertes,
        "justifications_a_jour": analyse.get("justifications_signature") == _signature(params, ajustements),
    }


def regenerer_justifications(analyse: dict, client, params: Parametres, ajustements: dict,
                             sauvegarder_cache: bool = True) -> None:
    tableau = calculer_tableau(analyse, params, ajustements)
    classement = [{
        "theme_id": l["theme_id"], "titre": l["titre"], "categorie_moscow": l["moscow"],
        "regle_appliquee": l["regle_appliquee"], "score_rice": round(l["score"], 2), "reach": l["nb_demandeurs"],
        "impact": l["impact"], "confidence": l["confidence"], "effort": l["effort"], "gravite_max": l["gravite_max"],
        "enjeux": l["enjeux"], "tendance": l["tendance"]["statut"], "nb_relances": l["nb_relances"],
    } for l in tableau["lignes"]]
    analyse["justifications"] = justifier(client, charger_contexte(), classement, params.capacite_sprint, tableau["points_must"])
    analyse["justifications_signature"] = _signature(params, ajustements)
    if sauvegarder_cache:
        sauvegarder(analyse)


def generer_user_stories(analyse: dict, client, theme_ids: list[str], params: Parametres, ajustements: dict,
                         progression=None) -> list[str]:
    """Rédige les User Stories des thèmes cochés. Renvoie la liste des erreurs éventuelles."""
    tableau = {l["theme_id"]: l for l in calculer_tableau(analyse, params, ajustements)["lignes"]}
    index_backlog = {b["id"]: b for b in charger_backlog()}
    erreurs = []
    for n, theme_id in enumerate(theme_ids, start=1):
        if progression:
            progression(f"Rédaction des User Stories ({n}/{len(theme_ids)})")
        l = tableau[theme_id]
        try:
            story = rediger(client, charger_contexte(), l, [analyse["feedbacks_index"][i] for i in l["ids_feedbacks"]],
                            index_backlog.get(l["backlog_id"] or ""), l["effort"] or 0)
            analyse["user_stories"][theme_id] = {**story, "theme_id": theme_id, "theme": l["titre"]}
        except Exception as e:  # une story en échec ne bloque pas les autres
            erreurs.append(f"{l['titre']} : {e}")
    sauvegarder(analyse)
    return erreurs


def sauvegarder(analyse: dict, chemin: Path = FICHIER_DERNIERE_ANALYSE) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(analyse, ensure_ascii=False, indent=1), encoding="utf-8")


def charger(chemin: Path = FICHIER_DERNIERE_ANALYSE) -> dict | None:
    if not chemin.exists():
        return None
    return json.loads(chemin.read_text(encoding="utf-8"))
