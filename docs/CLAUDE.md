# Contexte du projet : Copilote PO (POC)

## Pourquoi ce projet existe
Test technique **Product Builder** pour un entretien chez **Thiga** (cabinet de conseil).

Le sujet : concevoir un agent IA qui assiste le Product Owner d'une startup SaaS de gestion de projet sur trois tâches :
1. analyser les feedbacks clients multicanaux ;
2. prioriser les fonctionnalités (RICE, MoSCoW, avec justification) ;
3. rédiger les User Stories (critères d'acceptation, complexité).

Aucun jeu de données n'était fourni : nous l'avons créé.

**Livrables attendus**
- agent fonctionnel avec tests ;
- documentation de la démarche et des choix techniques ;
- restitution de 30 min : 10 min de démo, 5 min d'architecture, 5 min de démarche et difficultés, 10 min de questions.

**Grille d'évaluation**

| Critère | Poids |
|---|---|
| Compréhension métier | 20 % |
| Démarche (hypothèses, impasses, usage et contrôle de l'IA) | 20 % |
| Présentation | 20 % |
| Qualité technique | 15 % |
| Expérience utilisateur | 15 % |
| Complétude | 10 % |

Le jury pose des questions sur l'usage des assistants IA : **toute action de l'IA doit être traçable dans la documentation.**

**Contraintes du POC**
- Environ 1 jour de travail : rester proportionné.
- Livrables en français.
- Stack : Claude API (Sonnet 5.5), Streamlit en local.

## Principe directeur (à respecter dans toute modification)
**Le LLM propose, le code calcule, le PO décide.**
- Le LLM intervient seulement pour juger : classer (P1), regrouper (P2), estimer Impact, Confidence et Effort (P3), justifier le classement (P4), rédiger les User Stories (P5).
- Tout le reste est du Python déterministe et testé : filtrage, dédoublonnage, tendances, Reach, score RICE, MoSCoW, contrôles des sorties du LLM.
- Le PO peut ajuster toutes les valeurs ; le recalcul est instantané, sans appel au modèle.

## Documents de référence (font foi)
- `documentation_demarche.txt` : besoin, parcours Discovery / Strategy / Delivery / Growth, **règles de gestion R1 à R9 (section 2.5)**, démarche, pistes écartées, choix techniques. Copie de travail du livrable : **la tenir à jour à chaque changement**.
- `prompts_agent.md` : les 5 prompts, **validés par l'humain**. Les fichiers `prompts/*.txt` en sont la copie mot pour mot. **Ne pas modifier un prompt sans validation explicite de l'utilisateur**, et tracer la modification dans la doc.
- `prompt_developpement.md` : le prompt qui a servi à générer le code (proposé par l'IA, validé par l'humain).
- `data/prompt_generation_donnees.md` : le prompt qui a servi à générer le jeu de données.

## Règles de gestion (résumé ; le détail est dans la doc, section 2.5)

**R1 – Entrée.**
- Fichier de sauvegarde multicanal `data/feedbacks.json` : 50 feedbacks du 20/10 au 16/11/2026, sur 3 canaux, avec leurs dates d'origine.
- Boîte Gmail `contact@rodolphethienard.fr` en IMAP, dossier paramétrable (INBOX par défaut), mot-clé facultatif sur l'objet ou le contenu (insensible à la casse et aux accents). Les emails ont le canal « email ».
- Tickets JIRA Cloud lus par l'API REST v3 (`/rest/api/3/search/jql`), requête JQL paramétrable. Canal « ticket », source « JIRA » : les tickets du jeu de démo tiennent la place des vrais tickets JIRA et seraient retirés en production. Demandeur = rapporteur (`TODO À VALIDER` dans le README).

**R2 – Deux modes.**
- Connecté : appels à Claude, chaque appel mis en cache par empreinte.
- Hors ligne : rejoue `cache/derniere_analyse.json`.

**R3 – Filtrage.**
- `Question/Support` et `Non actionnable` sont écartés mais restent visibles ; le PO peut les réintégrer.
- Les demandes hors vision sont conservées et classées en Won't.

**R4 – Dédoublonnage.** Une demande par personne et par problème. La personne est identifiée par son email, à défaut par son pseudonyme (avis Play Store). La demande garde la gravité et l'enjeu les plus élevés. Le nombre de relances reste affiché.

**R5 – Tendance.**
- La période en cours (7 jours) se termine à la date de référence **incluse** : le 16/11/2026 pour la démo, le jour de l'analyse si Gmail ou JIRA est utilisé.
- Statuts : Nouveau ; En hausse ou En baisse si l'écart est d'au moins 2 messages ; Stable sinon.

**R6 – RICE.**
- Reach : demandeurs distincts.
- Impact : barème fixe selon la gravité (Bloquant 3, Majeur 2, Mineur 1, Cosmétique 0,5). Le LLM peut l'ajuster d'**un cran maximum**, avec justification ; le code le vérifie.
- Confidence : 50, 80 ou 100.
- Effort : suite de Fibonacci. L'estimation du backlog est reprise si l'élément couvre tout le besoin et n'est pas livré.
- Score = R^p1 × I^p2 × C^p3 / E^p4. Les poids sont réglables (1 par défaut, soit le RICE classique).

**R7 – MoSCoW** (paramètres réglables).
- Won't : hors vision.
- Must : d'abord les thèmes Bloquant + Rétention (règle activable), puis les autres par score décroissant, jusqu'à la capacité du sprint (35 points). Une alerte signale un dépassement.
- Should : thèmes suivants, dans la limite d'un sprint supplémentaire.
- Could : le reste.
- Le PO peut forcer une catégorie.

**R8 – User Stories.** Générées uniquement pour les thèmes cochés par le PO. Gherkin en français. Export JSON.

**R9 – Évaluation.**
- Comparaison avec `data/labels_attendus.json` : catégorie, gravité, enjeu, regroupement (thème majoritaire), pièges filtrés.
- Objectif indicatif : 80 % par mesure, 100 % pour le spam et les remerciements.

**R10 – Suivi et information des demandeurs** (`agent/suivi.py`).
- État : suivi du PO prioritaire, sinon déduit du backlog (À créer / Ticket créé / En cours (backlog) / Livré, insuffisant).
- Email sur action du PO uniquement : un envoi depuis Gmail, PO en destinataire, demandeurs en copie cachée ; seulement les adresses issues de Gmail ou JIRA (démo = fictives). Journal sans adresses dans `cache/suivi_po.json`.

**Classification**
- Catégorie : Bug / Demande de fonctionnalité / UX/Utilisabilité / Question/Support / Non actionnable.
- Gravité : Bloquant / Majeur / Mineur / Cosmétique.
- Enjeu business : Rétention / Adoption / Expansion / Efficacité.
- **Pas d'analyse de sentiment** : choix délibéré, justifié dans la doc.

## Jeu de démonstration (Orbiteam, entreprise fictive)
- 9 thèmes avec des tendances différentes :
  - SSO cassé depuis la v4.2 : 8 messages, 6 demandeurs, **Nouveau** ;
  - crash Android v3.8 : **En hausse** ;
  - notifications : **En baisse**, mais le problème n'est pas résolu (les utilisateurs ont coupé les notifications) ;
  - GitLab : 5 messages mais seulement 2 demandeurs, qui ont relancé et menacent de ne pas renouveler ;
  - export PDF, agenda Google, Kanban lent, export des temps, drag & drop Gantt.
- 8 pièges : 3 questions de support, spam, 2 remerciements, 2 demandes hors vision (paie, CRM). S'y ajoutent un feedback qui mélange deux problèmes et un problème de mot de passe qui ressemble au SSO sans en être.
- Les étiquettes de référence doivent être **relues et validées par l'humain** avant de s'en servir pour l'évaluation.

## État au 19/11/2026
**Fait**
- Code complet ; 61 tests pytest passent, sans réseau (`tests/faux_llm.py` simule le modèle à partir des étiquettes).
- Crédits API rechargés : analyses réelles depuis le 17/11. Itération 1 sur le prompt P1 (doute → gravité la plus élevée) : toutes les mesures d'évaluation dépassent 80 % (doc, étape 9).
- Lecture Gmail réelle constatée (analyse du 18/11 : 51 feedbacks, dont la boîte Gmail). Filtre par mot-clé, connecteur JIRA, onglet « Informer les clients » (R10), espace Monitoring et nouveau design ajoutés (doc, étape 10).
- Support de restitution de 12 slides (Artifact Slides, au style du modèle fourni par l'utilisateur) : https://claude.ai/artifact/PXnSYhjiUgCrv6XwB4kgAW. La démo se fait en direct dans l'application (doc, étape 11).

**Pas encore fait**
- Envoi réel d'un email (SMTP Gmail, R10) et lecture d'une vraie instance JIRA.
- Le SDK Anthropic actuel n'accepte plus le paramètre `temperature` : il n'est plus transmis, et la reproductibilité repose sur le cache.

**Prochaines étapes**
1. Tester l'envoi d'un email depuis l'onglet « Informer les clients » et, si possible, une vraie instance JIRA.
2. Répéter le déroulé : démo 10 min, architecture 5 min, démarche 5 min.

## Commandes
```bash
pip install -r requirements.txt
streamlit run app.py
pytest
python lancer_analyse.py [--gmail] [--dossier X] [--jours N] [--mot-cle M] [--jira] [--jql "..."]
python -m evaluation.evaluer
python -m tests.generer_demo_simulee
```

## Conventions
- Code, interface, messages et documentation en français. Noms de fonctions et de variables en français, cohérents avec la doc (thème, demande, gravité, enjeu…).
- Aucun secret dans le code, la doc, les logs ou le cache. Tout passe par `.env`, exclu du dépôt. **Ne jamais demander ni écrire la clé ou le mot de passe en clair.**
- Rester proportionné : pas de framework d'agents, pas de base de données, pas de base vectorielle. Le RAG est une piste d'amélioration pour le passage à l'échelle.
- Toute nouvelle règle de calcul : code déterministe et test associé.
- Toute réponse du LLM est validée par un schéma pydantic, avec une relance unique en cas d'échec.
- Si une règle métier manque, ne pas l'inventer : demander à l'utilisateur, ou laisser un `TODO À VALIDER` listé dans le README.
- Modifications dans `data_editor` : elles sont rattachées à l'identifiant du thème via `ss.ordre_editeur`, et l'éditeur est recréé à chaque changement (`version_editeur`), parce que le tableau se réordonne.
