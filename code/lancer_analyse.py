"""Lance une analyse complète en ligne de commande (mode connecté) et produit le cache de démonstration.

Usage :
    python lancer_analyse.py                 # fichier de sauvegarde seul (jeu de démonstration)
    python lancer_analyse.py --gmail         # fichier + boîte Gmail
    python lancer_analyse.py --gmail --dossier "Feedbacks" --jours 14
    python lancer_analyse.py --gmail --mot-cle Orbiteam   # seulement les emails qui contiennent ce mot
    python lancer_analyse.py --jira --jql "project = SUP AND created >= -14d"   # + tickets JIRA

L'analyse est enregistrée dans cache/derniere_analyse.json (rejouable en mode hors ligne dans l'interface),
puis évaluée par rapport aux étiquettes de référence (evaluation/rapport.md).
"""
from __future__ import annotations

import argparse
import sys
from datetime import date

from agent import pipeline
from agent.config import DATE_REFERENCE_DEMO, FICHIER_FEEDBACKS, RACINE, Parametres, lire_config_locale
from agent.llm import ClientLLM, transport_anthropic
from agent.sources import charger_fichier, filtrer_par_mot_cle, fusionner, lire_gmail, lire_jira
from evaluation.evaluer import evaluer, rapport_markdown


def main() -> None:
    args = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    args.add_argument("--gmail", action="store_true", help="ajouter les emails de la boîte Gmail")
    args.add_argument("--dossier", default=None, help="dossier Gmail (par défaut : GMAIL_DOSSIER ou INBOX)")
    args.add_argument("--jours", type=int, default=30, help="nombre de jours lus dans Gmail")
    args.add_argument("--mot-cle", default=None, help="ne garder que les emails dont l'objet ou le contenu contient ce mot")
    args.add_argument("--jira", action="store_true", help="ajouter les tickets JIRA")
    args.add_argument("--jql", default=None, help="requête JQL (par défaut : JIRA_JQL ou les 30 derniers jours)")
    args.add_argument("--sans-fichier", action="store_true", help="ne pas lire le fichier de sauvegarde")
    a = args.parse_args()

    cfg = lire_config_locale()
    if not cfg.cle_api:
        sys.exit("ANTHROPIC_API_KEY absente du fichier .env.")

    sources = [] if a.sans_fichier else [charger_fichier(FICHIER_FEEDBACKS)]
    if a.gmail:
        if not (cfg.gmail_adresse and cfg.gmail_mot_de_passe):
            sys.exit("GMAIL_ADRESSE ou GMAIL_APP_PASSWORD absent du fichier .env.")
        mails = lire_gmail(cfg.gmail_adresse, cfg.gmail_mot_de_passe, a.dossier or cfg.gmail_dossier, a.jours)
        print(f"{len(mails)} email(s) lu(s) dans Gmail.")
        if a.mot_cle:
            mails = filtrer_par_mot_cle(mails, a.mot_cle)
            print(f"{len(mails)} email(s) contiennent « {a.mot_cle} ».")
        sources.append(mails)
    if a.jira:
        if not (cfg.jira_url and cfg.jira_email and cfg.jira_jeton):
            sys.exit("JIRA_URL, JIRA_EMAIL ou JIRA_API_TOKEN absent du fichier .env.")
        tickets = lire_jira(cfg.jira_url, cfg.jira_email, cfg.jira_jeton, a.jql or cfg.jira_jql)
        print(f"{len(tickets)} ticket(s) JIRA lu(s).")
        sources.append(tickets)
    feedbacks = fusionner(*sources)

    params = Parametres(date_reference=date.today() if (a.gmail or a.jira) else DATE_REFERENCE_DEMO)
    client = ClientLLM(transport=transport_anthropic(cfg.cle_api))
    print(f"Analyse de {len(feedbacks)} feedbacks…")
    analyse = pipeline.analyser(feedbacks, client, params, progression=lambda m: print("  •", m))
    print(f"Terminé : {client.nb_appels_reels} appel(s) au modèle, {client.nb_depuis_cache} réponse(s) depuis le cache.")
    print(f"{len(analyse['ecartes'])} feedback(s) écarté(s), {len(analyse['themes'])} thème(s).")
    for alerte in analyse["alertes"]:
        print("  ⚠", alerte)

    texte = rapport_markdown(evaluer(analyse), analyse)
    (RACINE / "evaluation" / "rapport.md").write_text(texte, encoding="utf-8")
    print("\n" + texte)


if __name__ == "__main__":
    main()
