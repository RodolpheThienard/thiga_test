# Prompt de développement du POC

---

## 1. Mission

Développe le POC d'un agent IA qui assiste le Product Owner d'Orbiteam, un SaaS de gestion de projet fictif. L'agent :
1. analyse les feedbacks clients multicanaux ;
2. aide à les prioriser ;
3. rédige les User Stories.

Les documents de référence, joints au prompt, font foi :
- `documentation_demarche.txt` : besoin, parcours, **règles de gestion R1 à R9 (section 2.5)** ;
- `prompts_agent.md` : les 5 prompts du LLM, validés, **à reprendre mot pour mot** ;
- `data/` : jeu de démonstration (feedbacks, backlog, contexte produit, étiquettes de référence).

En cas de doute sur une règle métier, **ne l'invente pas** : applique la règle écrite, ou laisse un `# TODO À VALIDER` visible et signale-le dans le README.

**Principe d'architecture :** le LLM ne fait que ce qui demande du jugement (classer, regrouper, estimer, justifier, rédiger). Tout le reste est du code Python déterministe et testé : filtrage, dédoublonnage, tendances, Reach, score RICE, MoSCoW, contrôles.

**Contrainte de proportionnalité :** c'est un POC d'environ une journée.
- Pas de base de données, pas de framework d'agents (LangChain ou autre), pas de base vectorielle.
- Un pipeline explicite, lisible, en fonctions simples.

---

## 2. Stack

- Python 3.11, Streamlit (exécution locale), SDK `anthropic`, `pydantic` (validation des sorties), `python-dotenv`, `imaplib` (bibliothèque standard), `pytest`.
- Modèle : `claude-sonnet-5-5`.
- Interface, messages et sorties en français. Noms de fonctions et de variables en français, cohérents avec le vocabulaire de la documentation (thème, demande, gravité, enjeu…).

---

## 3. Structure du projet

```
orbiteam-agent/
├── app.py                   # interface Streamlit
├── agent/
│   ├── config.py            # paramètres par défaut + lecture du .env
│   ├── schemas.py           # modèles pydantic (feedback, fiche, demande, thème, estimation, user story)
│   ├── sources.py           # lecture du fichier JSON et de la boîte Gmail (R1)
│   ├── llm.py               # client Claude, validation JSON, relance, cache
│   ├── classification.py    # P1
│   ├── regroupement.py      # P2 + contrôles
│   ├── dedoublonnage.py     # R4
│   ├── tendances.py         # R5
│   ├── rice.py              # R6
│   ├── moscow.py            # R7
│   ├── justification.py     # P4
│   ├── user_stories.py      # P5 + export JSON (R8)
│   └── pipeline.py          # enchaînement des étapes, modes connecté / hors ligne (R2)
├── prompts/                 # P1 à P5, un fichier texte chacun, repris de prompts_agent.md
├── data/                    # jeu de démonstration (fourni)
├── cache/                   # résultats des analyses (mode hors ligne)
├── exports/                 # User Stories exportées
├── evaluation/evaluer.py    # R9
├── tests/
├── .env.example
├── .gitignore               # exclut .env, cache/ (sauf le cache de démo), exports/
├── requirements.txt
└── README.md
```

---

## 4. Configuration et secrets

`.env.example` (aucune valeur réelle) :
```
ANTHROPIC_API_KEY=
GMAIL_ADRESSE=contact@rodolphethienard.fr
GMAIL_APP_PASSWORD=
GMAIL_DOSSIER=INBOX
```

- Aucun secret dans le code, la documentation, les logs ou le cache.
- Si `ANTHROPIC_API_KEY` est absente : seul le mode hors ligne est proposé, avec un message clair.
- Si les identifiants Gmail sont absents ou invalides : la source Gmail est désactivée, avec un avertissement, et le reste fonctionne.

---

## 5. Pipeline (détail des règles en section 2.5 de la documentation)

**Étape 0 – Sources (R1)**
- Fichier `data/feedbacks.json` : canal et date d'origine conservés.
- Gmail en IMAP SSL (`imap.gmail.com:993`), dossier paramétrable, messages des N derniers jours (30 par défaut, réglable).
  - Pour chaque email, extraire : expéditeur (nom et adresse), objet, date (en-tête `Date`), corps texte (texte brut, ou HTML nettoyé à défaut).
  - Identifiant `MAIL-<uid>`, canal `email`.
- Les deux sources sont fusionnées dans un format commun.

**Étape 1 – Classification (P1)**
- Lots de 10.
- L'auteur et l'email ne sont **pas** envoyés au modèle.
- Chaque demande reçoit un identifiant `FB-xxx#n`.

**Étape 2 – Filtrage (R3)**
- Les catégories `Question/Support` et `Non actionnable` sont écartées et gardées à part, avec leur justification.

**Étape 3 – Regroupement (P2)**
- Contrôles par le code :
  - chaque demande actionnable apparaît dans exactement un thème ;
  - une demande oubliée est placée dans un thème « Non regroupé » et signalée ;
  - un doublon est retiré du second thème.
- Thèmes numérotés `TH-1`, `TH-2`…

**Étape 4 – Calculs par thème (code)**
- Nombre de messages.
- Demandeurs distincts : email, sinon nom d'auteur pour les avis sans email (R4).
- Nombre de relances.
- Gravité maximale et enjeux business.
- Tendance (R5) : période de 7 jours par défaut, seuil de 2, date de référence réglable.
  - Valeur par défaut de la date : le 17/11/2026 si seul le fichier est utilisé, sinon le jour de l'analyse.

**Étape 5 – Estimation (P3)**
- Pour tous les thèmes, sauf les thèmes hors vision.
- Contrôles par le code :
  - Impact sur l'échelle {0,25 ; 0,5 ; 1 ; 2 ; 3}, à un cran maximum de la base, sinon ramené à la base avec un signalement ;
  - Confidence ∈ {50, 80, 100} ;
  - Effort ∈ {1, 2, 3, 5, 8, 13, 21, 34} ;
  - l'estimation du backlog est reprise si elle existe.

**Étape 6 – Score RICE (R6)**
- Score = Reach^p1 × Impact^p2 × (Confidence/100)^p3 / Effort^p4. Poids réglables, à 1 par défaut.
- Toute valeur modifiée par le PO remplace celle du LLM.
- Le score se recalcule immédiatement, sans appel au modèle.

**Étape 7 – MoSCoW (R7)**
- Fonction pure, paramètres réglables.
- Won't : thèmes hors vision.
- Must :
  - d'abord, les thèmes Bloquant + Rétention (règle activable) ;
  - puis les autres thèmes par score décroissant, tant que la capacité n'est pas atteinte (35 points par défaut).
- Should : les thèmes suivants, dans la limite d'une capacité de sprint supplémentaire (nombre de sprints réglable, 1 par défaut).
- Could : le reste.
- Le PO peut forcer la catégorie d'un thème.
- La fonction renvoie, pour chaque thème, la `regle_appliquee` (texte court), et une alerte si les seuls Must forcés dépassent la capacité.

**Étape 8 – Justification (P4)**
- Le modèle explique le classement mais ne le modifie jamais.
- Si le PO modifie ensuite des valeurs, les justifications sont marquées « calculées avant modification ». Un bouton permet de les régénérer en mode connecté.

**Étape 9 – User Stories (P5)**
- Générées uniquement pour les thèmes cochés par le PO.
- Le PO peut modifier le texte de chaque User Story.
- Export JSON (téléchargement + copie dans `exports/`). Champs : identifiant, thème, titre, story, critères Gherkin, story points, hypothèses, écart avec l'effort RICE, découpage, questions ouvertes, hors périmètre, sources, date d'export.

---

## 6. Appels au LLM, cache et modes (R2)

**`llm.py` expose une seule fonction d'appel**, qui :
- charge le prompt depuis `prompts/` et injecte `contexte_produit.md` ;
- appelle Claude (température 0 pour P1 à P3, 0,3 pour P4 et P5) ;
- extrait et valide le JSON avec pydantic ;
- relance **une fois** en cas de réponse invalide, en renvoyant l'erreur de validation au modèle. En cas de second échec, lève une erreur explicite, que l'interface affiche sans planter.

**Cache**
- Chaque appel est mis en cache par empreinte (hash du prompt + des données envoyées), dans `cache/appels/`. Relancer la même analyse ne coûte donc rien.
- Chaque analyse complète est aussi sauvegardée dans `cache/derniere_analyse.json`.

**Mode hors ligne**
- Relit `cache/derniere_analyse.json`, ainsi que les User Stories en cache si elles existent. Aucun appel réseau.
- Les réglages (poids, capacité, modifications du PO) restent actifs, car ce sont des calculs locaux.
- Si le cache est absent, un message indique de lancer d'abord une analyse en mode connecté.

**Livrer avec le projet un cache de démonstration**, produit par une vraie exécution sur `data/feedbacks.json`.

---

## 7. Interface Streamlit

L'interface doit être utilisable par un PO sans explication. Elle comporte une barre latérale et quatre onglets.

**Barre latérale**
- Mode : Connecté / Hors ligne.
- Sources : fichier de sauvegarde (case à cocher), Gmail (case à cocher + dossier).
- Bouton « Lancer l'analyse ».
- Section repliable « Réglages » :
  - période et seuil de tendance, date de référence ;
  - poids RICE (curseurs de 0 à 2, pas de 0,25) ;
  - capacité du sprint ;
  - règle Bloquant + Rétention (activée ou non) ;
  - horizon Should ;
  - nombre de jours lus dans Gmail.

**Onglet 1 – Analyser**
- Indicateurs en tête : feedbacks reçus · écartés · analysés · thèmes.
- Tableau des thèmes : titre, messages, demandeurs, gravité max, enjeux, tendance (avec flèche), élément du backlog ou « Nouveau ». Le tableau est trié par défaut par gravité, puis par nombre de demandeurs.
- Pour chaque thème, un dépliant avec les feedbacks d'origine (identifiant, canal, date, extrait) et la justification du regroupement.
- Section « Feedbacks écartés » : motif de l'exclusion, et case « réintégrer ». Un feedback réintégré est traité comme actionnable à la prochaine analyse, en mode connecté.

**Onglet 2 – Prioriser**
- Tableau éditable : case « à rédiger », thème, MoSCoW (liste modifiable), score, Reach, Impact (base → proposé), Confidence, Effort, tendance.
- Impact, Confidence, Effort et MoSCoW sont modifiables. Tout est recalculé instantanément.
- Jauge de capacité : points en Must / capacité, alerte en cas de dépassement.
- Pour chaque thème, un dépliant avec les justifications : Impact, Confidence, Effort, MoSCoW et point d'attention.

**Onglet 3 – Rédiger**
- Pour les thèmes cochés : bouton « Générer les User Stories ».
- Affichage de chaque User Story :
  - story et critères Gherkin dans des blocs lisibles ;
  - points ;
  - questions ouvertes ;
  - découpage s'il y en a un.
- Champs modifiables et bouton « Exporter en JSON ».

**Onglet 4 – Qualité de l'agent**
- Résultats de l'évaluation (R9) sur le jeu de démonstration, avec le détail des erreurs.
- Si le jeu de démonstration n'est pas la source analysée, l'onglet l'indique.

*Note : l'onglet 4 s'ajoute aux trois onglets prévus dans la documentation, pour montrer en démo comment l'IA est contrôlée.*

---

## 8. Évaluation (R9) – `evaluation/evaluer.py`

Utilisable en ligne de commande et depuis l'onglet 4. Compare les résultats d'une analyse à `data/labels_attendus.json` :
- **Catégorie, gravité, enjeu** : précision par feedback. Pour un feedback à plusieurs demandes, comparer l'ensemble des valeurs.
- **Regroupement** : chaque thème de l'agent est associé au thème de référence majoritaire ; on mesure le pourcentage de feedbacks bien regroupés et on liste les erreurs.
- **Pièges** : taux de feedbacks Support et Non actionnable correctement écartés, et taux de demandes hors vision correctement marquées.
- **Sortie** : un tableau récapitulatif, avec l'objectif indicatif de 80 % par mesure et de 100 % pour le spam et les remerciements, plus la liste des erreurs. Le rapport est écrit dans `evaluation/rapport.md`.

---

## 9. Tests – `tests/`

Aucun appel réseau ni au LLM dans les tests : le client est simulé.

- `tendances` : nouveau, hausse, baisse, stable, cas limites du seuil et des bornes de période.
- `dedoublonnage` : relances de la même personne regroupées, gravité et enjeu maximum retenus, avis Play Store sans email identifiés par l'auteur.
- `rice` :
  - avec tous les poids à 1, on retrouve le RICE classique ;
  - effet d'un poids ;
  - Impact ramené à la base s'il s'écarte de plus d'un cran ;
  - valeurs hors échelle refusées ;
  - estimation du backlog reprise.
- `moscow` :
  - hors vision → Won't ;
  - règle Bloquant + Rétention ;
  - respect de la capacité ;
  - alerte de dépassement ;
  - forçage par le PO ;
  - horizon Should.
- `regroupement` : contrôles « une demande, un seul thème », demande oubliée, doublon.
- `llm` : JSON valide accepté ; JSON invalide → une relance puis une erreur explicite ; utilisation du cache.
- `sources` : lecture du JSON ; analyse d'un email IMAP simulé (texte et HTML) ; fusion des sources.

---

## 10. README

Le README doit contenir :
- l'installation ;
- la configuration du `.env`, avec la création d'un mot de passe d'application Gmail ;
- le lancement : `streamlit run app.py` ;
- le lancement des tests et de l'évaluation ;
- les deux modes ;
- la structure du projet ;
- la liste des `TODO À VALIDER` éventuels.

---

## 11. Critères de fin

1. `streamlit run app.py` fonctionne en mode hors ligne sans clé API, grâce au cache de démonstration.
2. En mode connecté, une analyse complète des 50 feedbacks aboutit, et un email envoyé à la boîte Gmail apparaît dans l'analyse suivante.
3. Les trois blocs fonctionnent de bout en bout : analyser → prioriser (modifier une valeur fait bouger le classement) → rédiger → exporter en JSON.
4. `pytest` passe intégralement.
5. `evaluation/evaluer.py` produit le rapport.
6. Aucun secret n'est présent dans le dépôt.

**Livre le code par étapes, en vérifiant chacune avant de passer à la suivante :**
1. calculs déterministes et leurs tests ;
2. appels au LLM et cache ;
3. pipeline ;
4. interface ;
5. évaluation et cache de démonstration.
