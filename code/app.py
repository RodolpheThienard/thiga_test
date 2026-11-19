"""Copilote PO – interface Streamlit.

Lancement : streamlit run app.py
"""
from __future__ import annotations

import json
from datetime import date

import pandas as pd
import streamlit as st

from agent import pipeline
from agent.config import (CATEGORIES_MOSCOW, CONFIDENCES, DOSSIER_CACHE, DATE_REFERENCE_DEMO, ECHELLE_IMPACT, FIBONACCI,
                          FICHIER_FEEDBACKS, GRAVITES, MODELE, Parametres, lire_config_locale)
from agent.llm import ClientLLM, transport_anthropic
from agent.sources import charger_fichier, filtrer_par_mot_cle, fusionner, lire_gmail, lire_jira
from agent.tendances import SYMBOLES
from agent.user_stories import exporter
from agent.suivi import (DEPLOYE, EN_COURS, charger_suivi, cle_suivi, destinataires, enregistrer_envoi,
                          envoyer_email, etat_theme, rediger_email)
from evaluation.evaluer import evaluer
import ui

st.set_page_config(page_title="Copilote PO · Orbiteam", page_icon="🧭", layout="wide")
ui.injecter_style()

COULEURS_MOSCOW = {"Must": "red", "Should": "orange", "Could": "blue", "Won't": "gray"}
ICONES_GRAVITE = {"Bloquant": "⛔", "Majeur": "🟧", "Mineur": "🟨", "Cosmétique": "⬜"}
ICONES_ETAT = {"À créer": "🔴", "Livré, insuffisant": "🟠", "Ticket créé": "🔵", "En cours (backlog)": "🟣",
               EN_COURS: "🟣", DEPLOYE: "🟢"}

cfg = lire_config_locale()
ss = st.session_state
def charger_cache():
    """Dernière analyse réelle ; à défaut, l'analyse simulée livrée pour explorer l'interface."""
    return pipeline.charger() or pipeline.charger(DOSSIER_CACHE / "demo_simulee.json")


if "analyse" not in ss:
    ss.analyse = charger_cache()
    ss.ajustements = {}
    ss.version_editeur = 0
    ss.reintegres = set((ss.analyse or {}).get("meta", {}).get("reintegres", []))


def reinitialiser_ajustements():
    ss.ajustements = {}
    ss.version_editeur += 1


# ---------------------------------------------------------------- Barre latérale
with st.sidebar:
    emplacement_marque = st.empty()
    connecte_possible = bool(cfg.cle_api)
    ui.section("Espaces")
    espace = st.radio("Espace", ["Parcours PO", "Monitoring de l'agent"], label_visibility="collapsed",
                      help="Parcours PO : analyser, prioriser, rédiger, informer. "
                           "Monitoring : qualité de l'agent et contrôles du code, à consulter à tout moment.")
    monitoring = espace.startswith("Monitoring")
    ui.section("Mode")
    mode = st.radio("Mode", ["Hors ligne (cache)", "Connecté (Claude)"], index=0, label_visibility="collapsed",
                    help="Hors ligne : rejoue la dernière analyse enregistrée, sans réseau. "
                         "Connecté : lit les sources et interroge Claude.")
    connecte = mode.startswith("Connecté")
    if connecte and not connecte_possible:
        st.error("Clé API absente du fichier .env : seul le mode hors ligne est disponible.")

    ui.section("Sources")
    src_fichier = st.checkbox("Fichier de sauvegarde multicanal", value=True, disabled=not connecte)
    gmail_possible = bool(cfg.gmail_adresse and cfg.gmail_mot_de_passe)
    src_gmail = st.checkbox("Boîte Gmail", value=False, disabled=not (connecte and gmail_possible),
                            help=None if gmail_possible else "Identifiants Gmail absents du fichier .env.")
    dossier_gmail = st.text_input("Dossier Gmail", value=cfg.gmail_dossier, disabled=not src_gmail)
    jours_gmail = st.number_input("Jours lus dans Gmail", 1, 365, 30, disabled=not src_gmail)
    mot_cle_gmail = st.text_input("Mot-clé (objet ou contenu)", value="", disabled=not src_gmail,
                                  placeholder="ex. Orbiteam — vide = tous les emails",
                                  help="Seuls les emails dont l'objet ou le contenu contient ce mot-clé sont analysés. "
                                       "Recherche insensible à la casse et aux accents.")

    jira_possible = bool(cfg.jira_url and cfg.jira_email and cfg.jira_jeton)
    src_jira = st.checkbox("Tickets JIRA", value=False, disabled=not (connecte and jira_possible),
                           help=None if jira_possible else "JIRA_URL, JIRA_EMAIL ou JIRA_API_TOKEN absent du fichier .env.")
    jql_jira = st.text_input("Requête JQL", value=cfg.jira_jql, disabled=not src_jira,
                             help="Sélection des tickets, ex. project = SUP AND created >= -30d")

    lancer = st.button("Lancer l'analyse" if connecte else "Charger la dernière analyse", type="primary",
                       width="stretch", disabled=connecte and not connecte_possible)

    ui.section("Paramètres")
    with st.expander("Réglages du calcul", expanded=False):
        st.markdown("**Tendances (R5)**")
        st.caption("La tendance compare le nombre de messages reçus sur une période récente "
                   "à celui de la période de même durée qui la précède.")
        sources_reelles = src_gmail or src_jira
        defaut_ref = date.today() if sources_reelles else DATE_REFERENCE_DEMO
        date_ref = st.date_input(
            "Fin de la période analysée", value=defaut_ref, key=f"date_ref_{sources_reelles}",
            help="Dernier jour (inclus) de la période récente. Par défaut : le 16/11/2026 pour le jeu de "
                 "démonstration, aujourd'hui quand Gmail ou JIRA est lu. Ex. 16/11 avec 7 jours : la période "
                 "récente va du 10/11 au 16/11 et elle est comparée au 03/11 → 09/11.")
        periode = st.slider("Durée de la période (jours)", 3, 30, 7,
                            help="Longueur de la période récente et de la période de comparaison.")
        seuil = st.slider("Écart pour « En hausse » / « En baisse » (messages)", 1, 5, 2,
                          help="En dessous de cet écart entre les deux périodes, la tendance est « Stable ».")
        st.markdown("**Poids du score RICE (R6)**")
        st.caption("Score = Reach^a × Impact^b × Confidence^c ÷ Effort^d. Les poids sont ces exposants. "
                   "**1** = RICE classique · **0** = critère ignoré · **2** = critère amplifié. "
                   "Exemple : avec un poids Reach à 2, un problème signalé par 6 personnes pèse 4 fois plus "
                   "qu'un problème signalé par 3, au lieu de 2 fois. Le classement se recalcule sans appel au modèle.")
        p_r = st.slider("Poids Reach (nombre de demandeurs)", 0.0, 2.0, 1.0, 0.25,
                        help="Plus haut : on favorise les problèmes qui touchent beaucoup de clients.")
        p_i = st.slider("Poids Impact (gravité)", 0.0, 2.0, 1.0, 0.25,
                        help="Plus haut : on favorise les problèmes graves, même rares.")
        p_c = st.slider("Poids Confidence (fiabilité de l'estimation)", 0.0, 2.0, 1.0, 0.25,
                        help="Plus haut : on pénalise davantage les problèmes mal compris.")
        p_e = st.slider("Poids Effort (coût de développement)", 0.0, 2.0, 1.0, 0.25,
                        help="Plus haut : on favorise les petits chantiers (« quick wins »). À 0, l'effort est ignoré.")
        st.markdown("**MoSCoW (R7)**")
        capacite = st.number_input("Capacité du sprint (points)", 5, 300, 35, step=5,
                                   help="Points disponibles pour les Must. Au-delà, une alerte s'affiche.")
        regle_br = st.toggle("Bloquant + Rétention = Must d'office", value=True,
                             help="Un problème bloquant qui menace la rétention passe en Must quel que soit son score.")
        horizon = st.number_input("Horizon Should (sprints)", 0, 5, 1,
                                  help="Nombre de sprints suivants à remplir avec les Should. Le reste passe en Could.")

    with emplacement_marque.container():
        ui.marque(connecte)
    ui.carte_sombre("Modèle", MODELE, "Prêt" if connecte_possible else "Clé API absente")

params = Parametres(periode_jours=periode, seuil_tendance=seuil, date_reference=date_ref,
                    poids_reach=p_r, poids_impact=p_i, poids_confidence=p_c, poids_effort=p_e,
                    capacite_sprint=int(capacite), regle_bloquant_retention=regle_br,
                    horizon_should_sprints=int(horizon))


def client_llm() -> ClientLLM:
    if connecte and connecte_possible:
        return ClientLLM(transport=transport_anthropic(cfg.cle_api))
    return ClientLLM(transport=None, hors_ligne=True)


# ---------------------------------------------------------------- Lancement
if lancer:
    if not connecte:
        ss.analyse = charger_cache()
        if ss.analyse is None:
            st.sidebar.error("Aucune analyse en cache : lancez d'abord une analyse en mode connecté.")
        reinitialiser_ajustements()
    else:
        feedbacks = []
        if src_fichier:
            feedbacks.append(charger_fichier(FICHIER_FEEDBACKS))
        if src_gmail:
            try:
                mails = lire_gmail(cfg.gmail_adresse, cfg.gmail_mot_de_passe, dossier_gmail, int(jours_gmail))
                retenus = filtrer_par_mot_cle(mails, mot_cle_gmail)
                feedbacks.append(retenus)
                filtre = f", {len(retenus)} contenant « {mot_cle_gmail.strip()} »" if mot_cle_gmail.strip() else ""
                st.sidebar.success(f"{len(mails)} email(s) lu(s) dans « {dossier_gmail} »{filtre}.")
            except Exception as e:
                st.sidebar.warning(f"Lecture Gmail impossible ({e}). Analyse poursuivie sans la boîte mail.")
        if src_jira:
            try:
                tickets = lire_jira(cfg.jira_url, cfg.jira_email, cfg.jira_jeton, jql_jira)
                feedbacks.append(tickets)
                st.sidebar.success(f"{len(tickets)} ticket(s) JIRA lu(s).")
            except Exception as e:
                st.sidebar.warning(f"Lecture JIRA impossible ({e}). Analyse poursuivie sans JIRA.")
        feedbacks = fusionner(*feedbacks)
        if not feedbacks:
            st.sidebar.error("Aucun feedback à analyser : cochez au moins une source.")
        else:
            try:
                with st.status(f"Analyse de {len(feedbacks)} feedbacks…", expanded=True) as statut:
                    analyse = pipeline.analyser(feedbacks, client_llm(), params, ss.reintegres,
                                                progression=lambda m: statut.write(m))
                    statut.update(label="Analyse terminée", state="complete", expanded=False)
                ss.analyse = analyse
                reinitialiser_ajustements()
            except Exception as e:
                st.error(f"L'analyse a échoué : {e}")

# ---------------------------------------------------------------- Monitoring de l'agent
def afficher_monitoring():
    """Écran de surveillance, hors du parcours : qualité de l'agent (R9) et contrôles du code."""
    st.markdown("## Monitoring de l'agent")
    st.caption(f"Analyse du {meta['date_analyse'].replace('T', ' à ')} · {meta['nb_feedbacks']} feedbacks · "
               f"modèle {meta.get('modele', MODELE)}. À consulter à tout moment, pas seulement en fin de cycle.")
    st.subheader("Contrôles du code sur les réponses de l'agent")
    if alertes_agent:
        for a in alertes_agent:
            st.write("• " + a)
    else:
        st.success("Aucune correction : toutes les réponses du modèle respectent les règles (Impact à un cran, "
                   "échelles, estimation du backlog).")
    st.subheader("Qualité de l'agent")
    st.caption("Comparaison des résultats de l'agent avec les étiquettes de référence, validées par l'humain "
               "(règle R9). C'est ainsi que l'on contrôle l'IA plutôt que de lui faire confiance.")
    if meta.get("simulee"):
        st.warning("Analyse simulée à partir des étiquettes : les scores ci-dessous sont mécaniquement à 100 % "
                   "et n'ont aucune valeur. Lancez une analyse connectée pour mesurer réellement l'agent.")
    resultat = evaluer(analyse)
    if resultat["nb_feedbacks_evalues"] == 0:
        st.info("L'analyse en cours ne porte pas sur le jeu de démonstration : pas d'étiquettes de référence.")
    else:
        if resultat["nb_feedbacks_evalues"] < meta["nb_feedbacks"]:
            st.caption(f"{meta['nb_feedbacks'] - resultat['nb_feedbacks_evalues']} feedback(s) hors jeu de "
                       "démonstration (ex. emails réels) ne sont pas évalués.")
        st.dataframe(pd.DataFrame([{
            "Mesure": m["mesure"], "Résultat": "—" if m["taux"] is None else f"{m['taux']:.0%}",
            "Détail": m["detail"], "Objectif": f"{m['objectif']:.0%}", "Atteint": "✅" if m["atteint"] else "❌",
        } for m in resultat["mesures"]]), hide_index=True, width="stretch")
        for nom, liste in resultat["erreurs"].items():
            if liste:
                with st.expander(f"Écarts – {nom} ({len(liste)})"):
                    for e in liste:
                        st.write("• " + e)


# ---------------------------------------------------------------- En-tête
analyse = ss.analyse
if analyse is None:
    ui.bandeau("Copilote PO · Orbiteam", "Analysez vos feedbacks clients",
               "Le LLM propose, le code calcule, le PO décide.")
    st.info("Aucune analyse disponible. Choisissez le mode **Connecté**, puis cliquez sur **Lancer l'analyse** "
            "(une clé API Anthropic est nécessaire dans le fichier `.env`). L'analyse est ensuite rejouable hors ligne.")
    st.stop()

meta = analyse["meta"]
tableau = pipeline.calculer_tableau(analyse, params, ss.ajustements)
lignes = tableau["lignes"]
par_id = {l["theme_id"]: l for l in lignes}
fbx = analyse["feedbacks_index"]
themes_utiles = [l for l in lignes if not l["hors_vision"]]
nb_must = sum(l["moscow"] == "Must" for l in themes_utiles)
alertes_agent = analyse.get("alertes", []) + [c for l in lignes for c in l["controles"]]
suivi_po = charger_suivi()
for l in lignes:
    l["etat"] = etat_theme(l.get("backlog_statut"), l.get("couverture_backlog"), suivi_po.get(cle_suivi(l)))

if monitoring:
    afficher_monitoring()
    st.stop()

date_analyse = pd.Timestamp(meta["date_analyse"])
ui.bandeau(
    f"Copilote PO · analyse du {date_analyse:%d/%m à %H:%M}",
    f"{nb_must} problème{'s' if nb_must > 1 else ''} à traiter ce sprint",
    f"{meta['nb_feedbacks']} feedbacks · {', '.join(meta['sources'])}. Le LLM propose, le code calcule, le PO décide.",
    "Analyse simulée : à remplacer par une analyse connectée avant la démo" if meta.get("simulee")
    else f"Sprint : {tableau['points_must']} / {params.capacite_sprint} points engagés",
    alerte=bool(meta.get("simulee")),
)
k1, k2, k3 = st.columns(3)
nb_ecartes = len(analyse["ecartes"])
nb_montants = sum(l["tendance"]["statut"] in ("Nouveau", "En hausse") for l in themes_utiles)
k1.markdown(ui.carte_kpi("boite", "#2F6FDE", "#E8F0FD", f"Feedbacks · {nb_ecartes} écartés",
                         str(meta["nb_feedbacks"])), unsafe_allow_html=True)
k2.markdown(ui.carte_kpi("calques", "#C2417A", "#FCE8F1", f"Problèmes · {nb_montants} en hausse ou nouveaux",
                         str(len(themes_utiles))), unsafe_allow_html=True)
k3.markdown(ui.carte_kpi("cible", "#1E7B4D", "#E3F6EC", f"Points en Must · sur {params.capacite_sprint}",
                         f"{tableau['points_must']} pts"), unsafe_allow_html=True)
st.write("")

onglet1, onglet2, onglet3, onglet4 = st.tabs(["Analyser", "Prioriser", "Rédiger", "Informer les clients"])


def libelle_tendance(t: dict) -> str:
    return f"{SYMBOLES[t['statut']]} {t['statut']} · {t['precedent']} → {t['courant']}"


# ---------------------------------------------------------------- 1. Analyser
with onglet1:
    st.subheader("Problèmes remontés par les clients")
    periode_t = lignes[0]["tendance"] if lignes else {"periode": "", "periode_precedente": ""}
    st.caption(f"Tendance : messages du {periode_t['periode_precedente']} → messages du {periode_t['periode']}. "
               "Demandeurs : une personne qui relance compte une fois (R4). "
               "État : 🔴 aucun ticket, à créer · 🟠 livré mais insuffisant · 🔵 ticket créé · 🟣 en cours · 🟢 corrigé.")
    tri = sorted(lignes, key=lambda l: (l["hors_vision"], -GRAVITES.index(l["gravite_max"]) if l["gravite_max"] else 0,
                                        -l["nb_demandeurs"]))
    st.dataframe(pd.DataFrame([{
        "Problème": ("🚫 " if l["hors_vision"] else "") + l["titre"],
        "État": "⚪ Hors vision" if l["hors_vision"] else f"{ICONES_ETAT.get(l['etat'], '')} {l['etat']}",
        "Gravité": f"{ICONES_GRAVITE.get(l['gravite_max'], '')} {l['gravite_max']}",
        "Demandeurs": l["nb_demandeurs"],
        "Récurrence": l["nb_messages"],
        "Enjeux": ", ".join(l["enjeux"]),
        "Tendance": libelle_tendance(l["tendance"]),
        "Backlog": l["backlog_id"] or "—",
    } for l in tri]), hide_index=True, width="stretch", column_config={
        "État": st.column_config.TextColumn(help="Où en est le traitement : backlog, puis suivi du PO (onglet Informer)."),
        "Gravité": st.column_config.TextColumn(help="La gravité la plus élevée parmi les demandes du problème."),
        "Demandeurs": st.column_config.NumberColumn(help="Personnes distinctes (R4)."),
        "Récurrence": st.column_config.NumberColumn(help="Messages reçus sur ce problème, relances comprises."),
        "Tendance": st.column_config.TextColumn(
            help=f"Messages du {periode_t['periode_precedente']} → messages du {periode_t['periode']}."),
        "Backlog": st.column_config.TextColumn(help="Élément du backlog qui traite le problème."),
    })

    st.subheader("Détail par problème")
    for l in tri:
        entete = (f"{SYMBOLES[l['tendance']['statut']]} {l['titre']} — {l['nb_demandeurs']} demandeur(s), "
                  f"{l['nb_messages']} message(s) · {l['gravite_max']}")
        with st.expander(entete):
            if l["description"]:
                st.write(l["description"])
            st.caption(f"**Pourquoi ce regroupement :** {l['justification']}")
            if l["backlog_id"]:
                couv = f" (couverture {l['couverture_backlog']})" if l.get("couverture_backlog") else ""
                st.caption(f"**Backlog :** {l['backlog_id']} – {l['backlog_titre']}{couv}")
            else:
                st.caption("**Backlog :** aucun élément existant, nouveau sujet.")
            if l["nb_relances"]:
                relanceurs = [f"{d['auteur']} ({d['nb_messages']} messages)" for d in l["demandeurs"] if d["nb_messages"] > 1]
                st.caption(f"**Relances :** {', '.join(relanceurs)}")
            st.dataframe(pd.DataFrame([{
                "ID": i, "Canal": fbx[i]["canal"], "Date": fbx[i]["date"].replace("T", " "),
                "Auteur": fbx[i].get("auteur"), "Message": fbx[i]["contenu"],
            } for i in l["ids_feedbacks"]]), hide_index=True, width="stretch")

    with st.expander(f"Feedbacks écartés ({len(analyse['ecartes'])}) – vérifier le filtrage"):
        st.caption("Questions de support, spam et remerciements ne vont pas dans le backlog. Cochez « réintégrer » "
                   "si un feedback a été écarté à tort : il sera traité comme actionnable à la prochaine analyse connectée.")
        for i in analyse["ecartes"]:
            fiche, fb = analyse["fiches"][i], fbx[i]
            col_a, col_b = st.columns([5, 1])
            col_a.markdown(f"**{i}** · {fiche['categorie']} · _{fb['contenu'][:160]}_  \n"
                           f"<small>{fiche['justification']}</small>", unsafe_allow_html=True)
            if col_b.checkbox("Réintégrer", value=i in ss.reintegres, key=f"reint_{i}"):
                ss.reintegres.add(i)
            else:
                ss.reintegres.discard(i)

# ---------------------------------------------------------------- 2. Prioriser
CHAMPS_EDITABLES = {"Rédiger": "rediger", "MoSCoW": "moscow", "Impact": "impact", "Conf. %": "confidence",
                    "Effort": "effort"}


def enregistrer_modifications():
    cle = f"editeur_{ss.version_editeur}"
    for ligne_idx, changements in ss[cle]["edited_rows"].items():
        theme_id = ss.ordre_editeur[int(ligne_idx)]
        aj = ss.ajustements.setdefault(theme_id, {})
        for colonne, valeur in changements.items():
            if colonne in CHAMPS_EDITABLES and valeur is not None:
                aj[CHAMPS_EDITABLES[colonne]] = valeur
    ss.version_editeur += 1


with onglet2:
    ratio = tableau["points_must"] / params.capacite_sprint
    col_a, col_b = st.columns([3, 1])
    col_a.markdown(f"**Sprint : {tableau['points_must']} / {params.capacite_sprint} points engagés en Must**")
    col_a.progress(min(ratio, 1.0))
    col_b.button("↺ Réinitialiser mes ajustements", on_click=reinitialiser_ajustements, width="stretch")
    for a in tableau["alertes"]:
        st.warning(a)

    st.caption("**Double-cliquez sur une cellule** pour forcer la catégorie MoSCoW ou modifier Impact, Confidence et "
               "Effort : le score et le classement se recalculent immédiatement. ✏️ = valeur ajustée par vous. "
               "Cochez « Rédiger » pour préparer les User Stories.")
    ss.ordre_editeur = [l["theme_id"] for l in lignes]
    df = pd.DataFrame([{
        "Rédiger": l["rediger"],
        "Rang": l["rang"],
        "MoSCoW": l["moscow"],
        "Problème": ("🚫 " if l["hors_vision"] else "") + l["titre"],
        "Score": round(l["score"], 2),
        "Reach": l["nb_demandeurs"],
        "Impact": l["impact"] if not l["hors_vision"] else pd.NA,
        "Conf. %": l["confidence"] if not l["hors_vision"] else pd.NA,
        "Effort": l["effort"] if not l["hors_vision"] else pd.NA,
        "Tendance": f"{SYMBOLES[l['tendance']['statut']]} {l['tendance']['statut']}",
        "Ajusté": "✏️" if l["ajuste"] else "",
    } for l in lignes])
    st.data_editor(
        df, key=f"editeur_{ss.version_editeur}", on_change=enregistrer_modifications,
        hide_index=True, width="stretch",
        disabled=["Rang", "Problème", "Score", "Reach", "Tendance", "Ajusté"],
        column_config={
            "Rédiger": st.column_config.CheckboxColumn(width="small"),
            "Rang": st.column_config.NumberColumn(width="small"),
            "Problème": st.column_config.TextColumn(width=290),
            "Reach": st.column_config.NumberColumn(help="Demandeurs distincts (R4)", width="small"),
            "Impact": st.column_config.SelectboxColumn(options=ECHELLE_IMPACT, help="Base fixe selon la gravité, ajustable d'un cran par le LLM"),
            "MoSCoW": st.column_config.SelectboxColumn(options=CATEGORIES_MOSCOW, required=True, width=95,
                                                      help="Double-cliquez pour forcer la catégorie (prioritaire sur les règles R7)"),
            "Conf. %": st.column_config.SelectboxColumn(options=CONFIDENCES, width="small"),
            "Effort": st.column_config.SelectboxColumn(options=FIBONACCI, width="small", help="Story points"),
            "Score": st.column_config.NumberColumn(format="%.2f",
                                                        help="Reach^p × Impact^p × Confidence^p / Effort^p"),
        },
    )

    st.subheader("Pourquoi ce classement ?")
    if not tableau["justifications_a_jour"]:
        c_a, c_b = st.columns([3, 1])
        c_a.info("Les explications ci-dessous ont été rédigées avant vos derniers ajustements ou réglages.")
        if c_b.button("Mettre à jour les explications", disabled=not (connecte and connecte_possible)):
            try:
                with st.spinner("Rédaction des explications…"):
                    pipeline.regenerer_justifications(analyse, client_llm(), params, ss.ajustements)
                st.rerun()
            except Exception as e:
                st.error(f"Échec : {e}")
    for l in lignes:
        j = l["justification_classement"]
        with st.expander(f":{COULEURS_MOSCOW[l['moscow']]}-badge[{l['moscow']}] {l['titre']} — score {l['score']:.2f}"):
            st.markdown(f"**Règle appliquée :** {l['regle_appliquee']}")
            if j.get("justification"):
                st.write(j["justification"])
            if j.get("point_attention"):
                st.warning("Point d'attention : " + j["point_attention"])
            if l["hors_vision"]:
                continue
            e = l["estimation"]
            st.markdown(
                f"- **Reach = {l['nb_demandeurs']}** demandeur(s) distinct(s) "
                f"({l['nb_messages']} messages, {l['nb_relances']} relance(s))\n"
                f"- **Impact = {l['impact']}** (base {l['impact_base']} pour « {l['gravite_max']} », proposé {l['impact_llm']}) — "
                f"{e.get('justification_impact') or 'base conservée'}\n"
                f"- **Confidence = {l['confidence']} %** — {e.get('justification_confidence', '')}\n"
                f"- **Effort = {l['effort']} points** — {e.get('justification_effort', '')} "
                f"{('_Hypothèses : ' + e['hypotheses_effort'] + '_') if e.get('hypotheses_effort') else ''}")
            for c in l["controles"]:
                st.caption("🛡️ " + c)

# ---------------------------------------------------------------- 3. Rédiger
with onglet3:
    coches = [l for l in lignes if l["rediger"]]
    if not coches:
        st.info("Cochez un ou plusieurs problèmes dans la colonne « Rédiger » de l'onglet **Prioriser**.")
    else:
        manquantes = [l["theme_id"] for l in coches if l["theme_id"] not in analyse["user_stories"]]
        c_a, c_b = st.columns([3, 1])
        c_a.write(f"**{len(coches)} problème(s) sélectionné(s)** : " + ", ".join(l["titre"] for l in coches))
        libelle = "Générer les User Stories" if manquantes else "Régénérer les User Stories"
        if c_b.button(libelle, type="primary", disabled=not (connecte and connecte_possible), width="stretch"):
            cibles = manquantes or [l["theme_id"] for l in coches]
            if not manquantes:
                for t in cibles:
                    analyse["user_stories"].pop(t, None)
            with st.status("Rédaction…", expanded=True) as statut:
                erreurs = pipeline.generer_user_stories(analyse, client_llm(), cibles, params, ss.ajustements,
                                                        progression=lambda m: statut.write(m))
                statut.update(label="Rédaction terminée", state="complete", expanded=False)
            for e in erreurs:
                st.error(e)
            st.rerun()
        if manquantes and not connecte:
            st.caption("En mode hors ligne, seules les User Stories déjà rédigées sont disponibles.")

        a_exporter = []
        for l in coches:
            us = analyse["user_stories"].get(l["theme_id"])
            if not us:
                continue
            t = l["theme_id"]
            with st.container(border=True):
                st.markdown(f"#### :{COULEURS_MOSCOW[l['moscow']]}-badge[{l['moscow']}] {l['titre']}")
                titre = st.text_input("Titre", us["titre"], key=f"us_titre_{t}")
                story = st.text_area("Story", us["story"], key=f"us_story_{t}", height=80)
                st.markdown("**Critères d'acceptation**")
                gherkin = "\n\n".join(f"Scénario : {c['scenario']}\n{c['gherkin']}" if not c["gherkin"].lstrip().startswith("Scénario")
                                      else c["gherkin"] for c in us["criteres_acceptation"])
                criteres = st.text_area("Gherkin", gherkin, key=f"us_gherkin_{t}", height=260, label_visibility="collapsed")
                c1, c2 = st.columns([1, 3])
                points = c1.selectbox("Story points", FIBONACCI, index=FIBONACCI.index(us["story_points"])
                                      if us["story_points"] in FIBONACCI else 3, key=f"us_points_{t}")
                c2.caption(f"**Hypothèses :** {us.get('hypotheses_estimation', '')}"
                           + (f"  \n**Écart avec l'effort RICE ({l['effort']} pts) :** {us['ecart_avec_effort_rice']}"
                              if us.get("ecart_avec_effort_rice") else ""))
                if us.get("decoupage"):
                    st.markdown("**Découpage proposé :**\n" + "\n".join(f"- {d}" for d in us["decoupage"]))
                if us.get("questions_ouvertes"):
                    st.markdown("**Questions ouvertes :**\n" + "\n".join(f"- {q}" for q in us["questions_ouvertes"]))
                if us.get("hors_perimetre"):
                    st.markdown("**Hors périmètre :**\n" + "\n".join(f"- {h}" for h in us["hors_perimetre"]))
                st.caption("Sources : " + ", ".join(us.get("sources", [])))
                a_exporter.append({
                    **us, "titre": titre, "story": story, "criteres_acceptation_gherkin": criteres,
                    "story_points": points, "moscow": l["moscow"], "score_rice": round(l["score"], 2),
                })
        if a_exporter:
            contenu = json.dumps({"produit": "Orbiteam", "user_stories": a_exporter}, ensure_ascii=False, indent=2)
            st.download_button("⬇️ Exporter en JSON", contenu, file_name="user_stories.json", mime="application/json",
                               type="primary", on_click=lambda: exporter(a_exporter))


# ---------------------------------------------------------------- 4. Informer les clients
with onglet4:
    st.caption("Prévenez les clients qui ont signalé un problème qu'il est pris en charge, puis que le correctif "
               "est déployé. Rien n'est envoyé sans votre clic. Un seul email part de la boîte Gmail du PO, "
               "les demandeurs en copie cachée : ils ne voient pas les adresses des autres.")
    candidats = [l for l in lignes if not l["hors_vision"]]
    if not candidats:
        st.info("Aucun problème à suivre dans cette analyse.")
    else:
        choix = st.selectbox(
            "Problème", [l["theme_id"] for l in candidats],
            format_func=lambda i: f"{par_id[i]['titre']} · {par_id[i]['nb_demandeurs']} demandeur(s) · {par_id[i]['etat']}")
        l = par_id[choix]
        adresses, nb_fictifs = destinataires(l["ids_feedbacks"], fbx)
        cle = cle_suivi(l)
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            c1.metric("État", l["etat"])
            c2.metric("Demandeurs", l["nb_demandeurs"])
            c3.metric("Destinataires réels", len(adresses))
            if not adresses:
                st.caption("Aucun demandeur joignable : seuls les emails de Gmail et les tickets JIRA portent une adresse "
                           "réelle. Les adresses du jeu de démonstration sont fictives et les avis des stores n'en ont pas. "
                           "Vous pouvez tout de même mettre à jour l'état du problème sans envoyer d'email.")
            elif nb_fictifs:
                st.caption(f"{nb_fictifs} demandeur(s) du jeu de démonstration ne sont pas contactés : "
                           "leurs adresses sont fictives.")
            type_message = st.radio("Message", [EN_COURS, DEPLOYE], horizontal=True,
                                    index=1 if l["etat"] in (EN_COURS, "En cours (backlog)") else 0)
            objet_defaut, corps_defaut = rediger_email(type_message, l["titre"])
            objet = st.text_input("Objet", objet_defaut, key=f"objet_{choix}_{type_message}")
            corps = st.text_area("Message", corps_defaut, height=230, key=f"corps_{choix}_{type_message}")
            gmail_ok = bool(cfg.gmail_adresse and cfg.gmail_mot_de_passe)
            relu = st.checkbox("J'ai relu le message", key=f"relu_{choix}_{type_message}")
            b1, b2 = st.columns(2)
            envoyer = b1.button(f"Envoyer à {len(adresses)} demandeur(s)", type="primary", width="stretch",
                                disabled=not (gmail_ok and adresses and relu),
                                help=None if gmail_ok else "Identifiants Gmail absents du fichier .env.")
            marquer = b2.button(f"Marquer « {type_message} » sans envoyer", width="stretch",
                                help="Met à jour l'état du problème sans prévenir les clients.")
            if envoyer:
                try:
                    envoyer_email(cfg.gmail_adresse, cfg.gmail_mot_de_passe, adresses, objet, corps)
                    enregistrer_envoi(cle, type_message, len(adresses))
                    st.success(f"Email envoyé à {len(adresses)} demandeur(s), avec vous en destinataire.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Envoi impossible : {e}")
            if marquer:
                enregistrer_envoi(cle, type_message, 0)
                st.rerun()
        historique = suivi_po.get(cle, {}).get("historique", [])
        if historique:
            st.markdown("**Historique**")
            for h in reversed(historique):
                envoi = f"email à {h['nb_destinataires']} demandeur(s)" if h["nb_destinataires"] else "sans envoi"
                st.caption(f"{h['date'].replace('T', ' à ')} · {h['statut']} · {envoi}")
