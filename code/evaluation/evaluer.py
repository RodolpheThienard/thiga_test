"""R9 – Évaluation de l'agent par rapport aux étiquettes de référence validées par l'humain.

Usage : python -m evaluation.evaluer   (évalue cache/derniere_analyse.json et écrit evaluation/rapport.md)
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from agent.config import CATEGORIES_ECARTEES, FICHIER_LABELS  # noqa: E402
from agent.dedoublonnage import gravite_max  # noqa: E402

OBJECTIF = 0.80


def _taux(ok: int, total: int) -> float | None:
    return ok / total if total else None


def evaluer(analyse: dict, labels: dict | None = None) -> dict:
    labels = labels or json.loads(FICHIER_LABELS.read_text(encoding="utf-8"))
    attendus = {l["id"]: l for l in labels["feedbacks"] if l["id"] in analyse["fiches"]}
    fiches, ecartes = analyse["fiches"], set(analyse["ecartes"])
    erreurs: dict[str, list[str]] = {"categorie": [], "gravite": [], "enjeu": [], "regroupement": [], "filtrage": [], "hors_vision": []}

    # 1. Catégorie, gravité, enjeu (feedback par feedback)
    ok_cat = ok_grav = ok_enj = n_dem = 0
    for i, l in attendus.items():
        f = fiches[i]
        if f["categorie"] == l["categorie"]:
            ok_cat += 1
        else:
            erreurs["categorie"].append(f"{i} : attendu « {l['categorie']} », obtenu « {f['categorie']} »")
        if l["gravite"] is None:
            continue
        n_dem += 1
        g = gravite_max([d["gravite"] for d in f["demandes"]])
        if g == l["gravite"]:
            ok_grav += 1
        else:
            erreurs["gravite"].append(f"{i} : attendu {l['gravite']}, obtenu {g or 'aucune demande'}")
        enjeux = {d["enjeu_business"] for d in f["demandes"]}
        if l["enjeu_business"] in enjeux:
            ok_enj += 1
        else:
            erreurs["enjeu"].append(f"{i} : attendu {l['enjeu_business']}, obtenu {', '.join(sorted(enjeux)) or 'aucune demande'}")

    # 2. Regroupement : chaque thème de l'agent est associé au thème de référence majoritaire.
    theme_de_demande = {d: t["theme_id"] for t in analyse["themes"] for d in t["demandes"]}
    majoritaire = {}
    for t in analyse["themes"]:
        compte = Counter(t_ref for d in t["demandes"] for t_ref in attendus.get(d.split("#")[0], {}).get("themes", []))
        majoritaire[t["theme_id"]] = compte.most_common(1)[0][0] if compte else None
    ok_reg = n_reg = 0
    for i, l in attendus.items():
        if not l["themes"]:
            continue
        n_reg += 1
        places = [majoritaire[theme_de_demande[d]] for d in theme_de_demande if d.split("#")[0] == i]
        if places and all(p in l["themes"] for p in places) and set(l["themes"]) <= set(places):
            ok_reg += 1
        else:
            erreurs["regroupement"].append(
                f"{i} : attendu {', '.join(l['themes'])}, placé dans {', '.join(map(str, places)) or 'aucun thème (écarté)'}")

    # 3. Pièges : filtrage et hors vision
    a_ecarter = [i for i, l in attendus.items() if l["categorie"] in CATEGORIES_ECARTEES]
    ok_filtre = sum(i in ecartes for i in a_ecarter)
    faux_ecartes = [i for i, l in attendus.items() if l["categorie"] not in CATEGORIES_ECARTEES and i in ecartes]
    for i in a_ecarter:
        if i not in ecartes:
            erreurs["filtrage"].append(f"{i} aurait dû être écarté ({attendus[i]['categorie']})")
    for i in faux_ecartes:
        erreurs["filtrage"].append(f"{i} écarté à tort")
    spam_merci = [i for i in a_ecarter if attendus[i]["categorie"] == "Non actionnable"]
    hv = [i for i, l in attendus.items() if "HV" in l["themes"]]
    ok_hv = 0
    for i in hv:
        if any(d["hors_vision"] for d in fiches[i]["demandes"]):
            ok_hv += 1
        else:
            erreurs["hors_vision"].append(f"{i} n'a pas été marqué hors vision")

    mesures = [
        ("Catégorie", _taux(ok_cat, len(attendus)), f"{ok_cat}/{len(attendus)}", OBJECTIF),
        ("Gravité", _taux(ok_grav, n_dem), f"{ok_grav}/{n_dem}", OBJECTIF),
        ("Enjeu business", _taux(ok_enj, n_dem), f"{ok_enj}/{n_dem}", OBJECTIF),
        ("Regroupement en thèmes", _taux(ok_reg, n_reg), f"{ok_reg}/{n_reg}", OBJECTIF),
        ("Pièges écartés (support, spam, remerciements)", _taux(ok_filtre, len(a_ecarter)), f"{ok_filtre}/{len(a_ecarter)}", OBJECTIF),
        ("Spam et remerciements écartés", _taux(sum(i in ecartes for i in spam_merci), len(spam_merci)),
         f"{sum(i in ecartes for i in spam_merci)}/{len(spam_merci)}", 1.0),
        ("Feedbacks utiles conservés", _taux(len(attendus) - len(a_ecarter) - len(faux_ecartes), len(attendus) - len(a_ecarter)),
         f"{len(attendus) - len(a_ecarter) - len(faux_ecartes)}/{len(attendus) - len(a_ecarter)}", OBJECTIF),
        ("Demandes hors vision marquées", _taux(ok_hv, len(hv)), f"{ok_hv}/{len(hv)}", OBJECTIF),
    ]
    return {
        "nb_feedbacks_evalues": len(attendus),
        "mesures": [{"mesure": m, "taux": t, "detail": d, "objectif": o, "atteint": t is not None and t >= o}
                    for m, t, d, o in mesures],
        "erreurs": erreurs,
    }


def rapport_markdown(resultat: dict, analyse: dict) -> str:
    lignes = [
        "# Rapport d'évaluation de l'agent", "",
        f"Analyse du {analyse['meta']['date_analyse']} · modèle {analyse['meta']['modele']} · "
        f"{resultat['nb_feedbacks_evalues']} feedbacks comparés aux étiquettes de référence.", "",
        "| Mesure | Résultat | Détail | Objectif | Atteint |", "|---|---|---|---|---|",
    ]
    for m in resultat["mesures"]:
        taux = "—" if m["taux"] is None else f"{m['taux']:.0%}"
        lignes.append(f"| {m['mesure']} | {taux} | {m['detail']} | {m['objectif']:.0%} | {'✅' if m['atteint'] else '❌'} |")
    lignes += ["", "## Écarts constatés", ""]
    for nom, liste in resultat["erreurs"].items():
        lignes.append(f"**{nom.capitalize()}** : {len(liste)} écart(s)")
        lignes += [f"- {e}" for e in liste]
        lignes.append("")
    return "\n".join(lignes)


if __name__ == "__main__":
    from agent.pipeline import charger

    analyse = charger()
    if analyse is None:
        sys.exit("Aucune analyse en cache : lancez d'abord une analyse.")
    resultat = evaluer(analyse)
    texte = rapport_markdown(resultat, analyse)
    (RACINE / "evaluation" / "rapport.md").write_text(texte, encoding="utf-8")
    print(texte)
