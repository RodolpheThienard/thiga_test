# Copilote PO – agent IA d'aide au Product Owner (POC)

Agent qui assiste le Product Owner d'**Orbiteam** (SaaS de gestion de projet fictif) sur trois tâches :

1. **Analyser** les feedbacks multicanaux : classification, filtrage des pièges, regroupement en problèmes, tendances.
2. **Prioriser** : score RICE et répartition MoSCoW, réglables et ajustables par le PO.
3. **Rédiger** les User Stories des problèmes choisis (critères Gherkin, story points), avec export JSON.

> Principe : **le LLM propose, le code calcule, le PO décide.**
> Claude intervient uniquement là où il faut du jugement : classer, regrouper, estimer, justifier, rédiger.
> Le filtrage, le dédoublonnage, les tendances, le score RICE, la répartition MoSCoW et le contrôle des réponses du modèle sont du code Python déterministe et testé.

La démarche, les règles de gestion (R1 à R9) et les choix techniques sont détaillés dans `../docs/documentation_demarche.txt`. Les prompts du modèle sont décrits dans `../docs/prompts_agent.md` et se trouvent dans `prompts/`.

---

## Installation

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # puis compléter .env
```

### Configuration (`.env`)

| Variable | Rôle |
|---|---|
| `ANTHROPIC_API_KEY` | Clé API Anthropic (mode connecté). Sans clé, seul le mode hors ligne est disponible. |
| `GMAIL_ADRESSE` | Boîte Gmail lue en IMAP. |
| `GMAIL_APP_PASSWORD` | **Mot de passe d'application** Gmail, pas le mot de passe du compte. |
| `GMAIL_DOSSIER` | Dossier lu (par défaut `INBOX`). |
| `JIRA_URL` | Adresse du site JIRA Cloud, ex. `https://votre-site.atlassian.net` (facultatif). |
| `JIRA_EMAIL` | Compte Atlassian qui lit les tickets. |
| `JIRA_API_TOKEN` | **Jeton API** Atlassian, pas le mot de passe du compte. |
| `JIRA_JQL` | Tickets lus (par défaut `created >= -30d ORDER BY created DESC`). |

**Créer le mot de passe d'application Gmail :**
1. Compte Google → Sécurité → activer la validation en deux étapes.
2. Toujours dans Sécurité, ouvrir « Mots de passe des applications » et en créer un nommé « Copilote PO ».
3. Copier les 16 lettres dans `GMAIL_APP_PASSWORD`.

L'accès IMAP doit être activé dans les paramètres Gmail.

**Créer le jeton API JIRA :** sur https://id.atlassian.com/manage-profile/security/api-tokens, « Créer un jeton d'API », puis le copier dans `JIRA_API_TOKEN`. Le compte doit avoir accès en lecture aux projets visés par la requête JQL.

Le fichier `.env` est exclu du dépôt (`.gitignore`). Aucun secret n'est écrit dans le code, les logs ou le cache.

---

## Lancement

```bash
streamlit run app.py
```

### Deux modes (R2)

| Mode | Fonctionnement |
|---|---|
| **Connecté** | Lit le fichier de sauvegarde et/ou la boîte Gmail, interroge Claude (`claude-sonnet-5-5`). L'analyse est enregistrée dans `cache/derniere_analyse.json`, et chaque réponse du modèle est mise en cache dans `cache/appels/`. |
| **Hors ligne** | Rejoue la dernière analyse, sans réseau ni appel au modèle. Les réglages et les ajustements du PO restent actifs, car ce sont des calculs locaux. |

**Première utilisation.** Tant qu'aucune analyse réelle n'a été lancée, l'interface affiche une **analyse simulée** (`cache/demo_simulee.json`), clairement signalée par un bandeau. Elle est construite à partir des étiquettes de référence, sans appel au modèle, et ne sert qu'à explorer l'interface.

**Avant la démonstration**, produire le vrai cache :

```bash
python lancer_analyse.py            # jeu de démonstration (50 feedbacks)
python lancer_analyse.py --gmail    # + emails de la boîte Gmail
python lancer_analyse.py --gmail --mot-cle Orbiteam   # + seulement les emails qui contiennent « Orbiteam »
python lancer_analyse.py --jira --jql "project = SUP"  # + tickets JIRA
```

La commande affiche aussi le rapport d'évaluation, écrit dans `evaluation/rapport.md`.

### L'interface

- **Barre latérale** : mode, sources, lancement de l'analyse et réglages :
  - date de référence, période et seuil des tendances ;
  - poids RICE ;
  - capacité du sprint ;
  - règle Bloquant + Rétention ;
  - horizon Should.
En tête de page : un bandeau de synthèse (problèmes à traiter ce sprint) et trois indicateurs. La barre latérale sépare deux espaces : le **parcours PO** (4 onglets) et le **Monitoring de l'agent**.

- **Analyser** : problèmes remontés (état, gravité, demandeurs distincts, récurrence, tendance, lien avec le backlog), détail des feedbacks par problème, feedbacks écartés avec possibilité de les réintégrer.
- **Prioriser** : tableau éditable (Impact, Confidence, Effort, MoSCoW). Le classement se recalcule instantanément. La jauge montre la capacité du sprint. Pour chaque problème, une explication du classement : règle appliquée, justification, point d'attention, détail RICE.
- **Rédiger** : User Stories des problèmes cochés, modifiables, exportées en JSON (téléchargement et copie dans `exports/`).
- **Informer les clients** : email aux demandeurs d'un problème (« en cours de traitement », puis « correctif déployé »), envoyé depuis la boîte Gmail du PO en copie cachée, après relecture. Ou simple mise à jour de l'état, sans envoi (R10).
- **Monitoring de l'agent** (espace séparé) : contrôles du code sur les réponses du modèle et comparaison aux étiquettes de référence (R9).

---

## Tests et évaluation

```bash
pytest                                # 61 tests, sans réseau ni appel au modèle (faux transport)
python -m evaluation.evaluer          # évalue cache/derniere_analyse.json → evaluation/rapport.md
```

Ce que couvrent les tests :
- **Tendances** : nouveau, hausse, baisse, stable, bornes, seuil, période.
- **Dédoublonnage** par personne.
- **RICE** : poids, contrôle de l'Impact (un cran maximum autour de la base), échelles, reprise de l'estimation du backlog.
- **MoSCoW** : hors vision, Bloquant + Rétention, capacité, alerte, forçage par le PO, horizon.
- **Contrôles du regroupement**.
- **Client LLM** : validation, relance unique, cache, mode hors ligne.
- **Sources** : fichier, email texte et HTML, fusion.
- **Pipeline** de bout en bout.
- **Évaluation**.

---

## Structure

```
app.py                  interface Streamlit
ui.py                   habillage : feuille de style, bandeau, cartes
lancer_analyse.py       analyse en ligne de commande (production du cache de démonstration)
agent/
  config.py             paramètres par défaut (règles R1 à R9), lecture du .env
  schemas.py            schémas pydantic des réponses du modèle
  sources.py            fichier de sauvegarde + Gmail IMAP (R1)
  llm.py                client Claude : prompts, validation JSON, relance unique, cache (R2)
  classification.py     P1 + filtrage (R3)
  regroupement.py       P2 + contrôles (une demande = un thème)
  dedoublonnage.py      R4 : une demande par personne et par problème
  suivi.py              R10 : état des problèmes, emails aux demandeurs
  tendances.py          R5
  rice.py               R6 : contrôles et score pondéré
  moscow.py             R7
  justification.py      P3 (estimation) et P4 (explication du classement)
  user_stories.py       P5 + export JSON (R8)
  pipeline.py           enchaînement des étapes, recalcul instantané
prompts/                P1 à P5, validés par l'humain
data/                   jeu de démonstration, backlog, contexte produit, étiquettes de référence
evaluation/evaluer.py   R9
tests/                  tests automatiques + faux modèle + génération de l'analyse simulée
```

## Points à valider (`TODO À VALIDER`)

- **Température** : le SDK Anthropic actuel ne permet plus de la régler. Elle n'est donc pas transmise, et la reproductibilité est assurée par le cache.
- **Date de référence de la démonstration** : le **16/11/2026**, compté comme le dernier jour inclus de la période en cours (période du 10/11 au 16/11).
- **Réintégration d'un feedback écarté** : elle prend effet à l'analyse connectée suivante.
- **Demandeur d'un ticket JIRA** : c'est le rapporteur du ticket. Si les tickets sont saisis par l'équipe support au nom des clients, le rapporteur est l'agent support et le Reach serait sous-estimé : il faudrait alors lire un autre champ (ex. « Demandeur » de JIRA Service Management, ou un champ personnalisé).
- **État d'un problème (R10)** : la correspondance avec le backlog (« À faire » = Ticket créé, etc.) et le texte des emails sont des propositions de l'IA, à confirmer.
