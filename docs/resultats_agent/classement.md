# Classement des problèmes – dernière analyse réelle

Analyse produite par l'agent (Claude Sonnet 5.5) ; classement recalculé par le code avec les réglages par défaut (poids RICE à 1, capacité du sprint 35 points, règle Bloquant + Rétention active). Points engagés en Must : 31 / 35.

| Rang | MoSCoW | Problème | Score | Reach | Impact | Conf. | Effort | Gravité | Tendance |
|---:|---|---|---:|---:|---:|---:|---:|---|---|
| 1 | Must | L'application Android plante à l'ouverture d'une tâche avec pièces jointes | 4.00 | 4 | 3 | 100 | 3 | Bloquant | En hausse (1 → 3) |
| 2 | Must | Connexion SSO impossible puis déconnexions répétées depuis la v4.2 | 3.60 | 6 | 3 | 100 | 5 | Bloquant | Nouveau (0 → 8) |
| 3 | Must | Trop de notifications email, sans choix des événements à recevoir | 1.60 | 4 | 2 | 100 | 5 | Majeur | En baisse (2 → 0) |
| 4 | Must | L'export PDF du planning n'est pas présentable (coupures, pas de logo) | 1.00 | 4 | 2 | 100 | 8 | Majeur | Stable (1 → 2) |
| 5 | Must | Échéances et jalons absents de Google Agenda et Outlook | 1.00 | 4 | 2 | 100 | 8 | Majeur | Stable (1 → 1) |
| 6 | Must | L'application plante systématiquement, contexte non précisé | 0.75 | 1 | 3 | 50 | 2 | Bloquant | Nouveau (0 → 1) |
| 7 | Should | Impossible d'exporter les heures par client, mois et collaborateur pour facturer | 0.64 | 2 | 2 | 80 | 5 | Majeur | Stable (0 → 1) |
| 8 | Should | Le Kanban est très lent à charger sur les gros projets | 0.60 | 3 | 2 | 80 | 8 | Majeur | Stable (1 → 2) |
| 9 | Should | Pas d'intégration GitLab : double saisie et risque de départ | 0.37 | 2 | 3 | 80 | 13 | Majeur | Stable (1 → 1) |
| 10 | Could | Créer des dépendances entre tâches dans le Gantt est trop long | 0.23 | 3 | 2 | 80 | 21 | Majeur | Stable (1 → 0) |
| 11 | Won't | Gérer les fiches de paie et les congés dans Orbiteam | 0.00 | 1 | — | — | 0 | Mineur | Stable (0 → 0) |
| 12 | Won't | Suivre ses prospects commerciaux directement dans Orbiteam | 0.00 | 1 | — | — | 0 | Mineur | Nouveau (0 → 1) |

## Justifications

### 1. L'application Android plante à l'ouverture d'une tâche avec pièces jointes — Must
- **Justification** : Le thème est Bloquant avec un enjeu Rétention, ce qui le classe en Must d'office, quel que soit son score. Son score RICE de 4,0 est le plus élevé de la liste, avec 4 demandeurs et un effort de 3 points.
- *Impact* : Base Bloquant conservée, déjà au maximum : les utilisateurs Android ne peuvent plus consulter les tâches avec pièces jointes, au point de repasser sur le navigateur mobile (FB-037).
- *Confidence* : Quatre demandeurs décrivent le même crash depuis la v3.8, et la cause est identifiée : la nouvelle visionneuse de pièces jointes livrée le 7/11.
- *Effort* : Correctif ciblé sur un composant précis (la visionneuse), avec reproduction, test sur plusieurs appareils Android et publication d'une version corrective.

### 2. Connexion SSO impossible puis déconnexions répétées depuis la v4.2 — Must
- **Justification** : Le thème est Bloquant avec un enjeu Rétention, donc Must d'office. Il touche le plus grand nombre de demandeurs (6), pour un effort de 5 points.
- **Point d'attention** : Deux relances client ont eu lieu. Son score (3,6) est inférieur à celui de TH-9, mais cet écart ne change rien : la règle du Bloquant s'applique dans les deux cas.
- *Impact* : Base Bloquant conservée, déjà au maximum : 30 personnes bloquées pendant deux jours (FB-030, FB-046), une solution alternative envisagée (FB-034), et un incident bloquant non résolu sous 48 h contraire à l'objectif de fiabilité.
- *Confidence* : Six demandeurs concordants et un déclencheur évident : la mise en production v4.2 du 9/11 (bibliothèques d'authentification et durée de session) précède l'erreur SAML puis les déconnexions répétées (FB-036, FB-041).
- *Effort* : Il s'agit de correctifs ciblés sur l'authentification (validation SAML après mise à jour de bibliothèques, durée de session) à valider avec plusieurs fournisseurs d'identité, auxquels s'ajoute le retour écrit sur la cause exigé par FB-046.

### 3. Trop de notifications email, sans choix des événements à recevoir — Must
- **Justification** : Le thème est Must grâce à un score de 1,6 (4 demandeurs, impact 2, effort 5) et il rentre dans la capacité du sprint. Sa gravité est Majeure, pas Bloquante.
- **Point d'attention** : La tendance est en baisse alors que le problème n'est pas résolu : les clients ont peut-être simplement cessé de le signaler. Un client a aussi relancé une fois.
- *Impact* : Base Majeur conservée : le problème est réel (FB-002, FB-024 : une échéance client ratée après désactivation des notifications) mais ne bloque pas l'usage de l'outil et la tendance est en baisse.
- *Confidence* : Quatre demandeurs formulent le même besoin (filtrer par événement, mentions, tâches assignées, résumé quotidien), et la cause est évidente : aucun réglage de notifications n'existe.
- *Effort* : Estimation reprise telle quelle du backlog.

### 4. L'export PDF du planning n'est pas présentable (coupures, pas de logo) — Must
- **Justification** : Le thème est Must parce que son score de 1,0 est élevé par rapport au reste du backlog et qu'il rentre dans la capacité du sprint. Il est Majeur, pas Bloquant, avec 4 demandeurs et un effort de 8 points.
- **Point d'attention** : Deux relances ont eu lieu. Avec 8 points, c'est l'un des deux plus gros postes du sprint : son statut de Must repose sur le fait qu'il rentre dans la capacité, pas sur une règle d'office.
- *Impact* : Base Majeur conservée : les équipes refont les supports à la main avant chaque comité (FB-003 : une heure à chaque fois, FB-021), mais aucun lien explicite avec un renouvellement ou avec les objectifs du trimestre.
- *Confidence* : Quatre demandeurs et six messages concordants décrivent les mêmes défauts : coupures de pages, noms tronqués, absence de logo et de mise en forme.
- *Effort* : Il faut revoir la pagination du rendu PDF du Gantt et des jalons, ajouter l'orientation, le format de page (A3, ajustement à la page) et le logo, ce qui demande un travail de mise en page non trivial et des tests visuels.

### 5. Échéances et jalons absents de Google Agenda et Outlook — Must
- **Justification** : Le thème est Must avec un score de 1,0 (4 demandeurs, impact 2) et il rentre dans la capacité du sprint. Les enjeux concernés sont l'Expansion et l'Efficacité.
- **Point d'attention** : Avec 8 points d'effort, il pèse lourd sur les 31 points déjà engagés. Comme pour TH-2, son statut de Must dépend de la capacité du sprint, pas d'une règle d'office.
- *Impact* : Base Majeur conservée : des deadlines passent inaperçues (FB-009, FB-028) et FB-009 évoque une extension de 15 utilisateurs, mais il n'y a pas de menace de départ.
- *Confidence* : Quatre demandeurs réclament la même chose (échéances et jalons dans Google Agenda ou Outlook) et le besoin est évident.
- *Effort* : Estimation reprise telle quelle du backlog.

### 6. L'application plante systématiquement, contexte non précisé — Must
- **Justification** : Le thème est Bloquant avec un enjeu Rétention, donc Must d'office, malgré un score de seulement 0,75. Il ne compte qu'un demandeur et une confiance de 50 %, pour un effort de 2 points.
- **Point d'attention** : Le thème est Must par la seule règle du Bloquant. Il repose sur un unique signalement, nouveau, au contexte non précisé et à confiance faible. Il vaut la peine de le qualifier avant d'y consacrer les 2 points.
- *Impact* : Base Bloquant conservée sans ajustement ; l'incertitude sur la réalité du problème est portée par la confiance et non par l'impact.
- *Confidence* : Un seul avis de 1 étoile (FB-042), sans plateforme, version ni action concernée, qui peut ou non correspondre à la régression Android (TH-9).
- *Effort* : L'effort correspond uniquement à une qualification : analyse des journaux de crash, tentative de reproduction et recontact de l'utilisateur.

### 7. Impossible d'exporter les heures par client, mois et collaborateur pour facturer — Should
- **Justification** : Le thème est Should : il ne rentre pas dans le sprint, mais il rentre dans l'horizon Should. Son score est de 0,64, avec 2 demandeurs, un effort de 5 points et une gravité Majeure.
- **Point d'attention** : Il reste 4 points de capacité (35 moins 31) et ce thème en demande 5. Il manque donc 1 point, et un client a déjà relancé.
- *Impact* : Base Majeur conservée : le défaut impose du copier-coller à chaque clôture mensuelle (FB-043 : une demi-journée de consultants), sans enjeu de rétention déclaré ; la facturation reste hors vision, mais fournir les données exportables entre dans le périmètre.
- *Confidence* : Le besoin est clair (export CSV détaillé par client, mois et collaborateur), mais seuls deux demandeurs s'expriment.
- *Effort* : Il s'agit d'enrichir un export existant avec des agrégations et des filtres sur des données de temps déjà collectées, ce qui est un développement de taille moyenne.

### 8. Le Kanban est très lent à charger sur les gros projets — Should
- **Justification** : Le thème est Should : il ne rentre pas dans le sprint (8 points d'effort pour 4 restants), mais il rentre dans l'horizon Should. Son score est de 0,6, avec 3 demandeurs et une gravité Majeure.
- **Point d'attention** : La tendance est en hausse et il y a eu deux relances. Le problème semble s'aggraver, et le classement Should ne reflète pas cette dynamique.
- *Impact* : Base Majeur conservée : le Kanban devient quasi inutilisable sur les gros projets et des équipes retournent sur des tableurs (FB-038, MAIL-22180), la tendance est en hausse, mais aucun renouvellement n'est explicitement menacé.
- *Confidence* : Le symptôme est clair et constaté par trois demandeurs, mais la cause est incertaine : FB-012 et FB-026 pointent le volume de cartes, tandis que MAIL-22180 signale une dégradation récente sur seulement 400 tâches, qui pourrait être une régression.
- *Effort* : Il faut d'abord diagnostiquer (requêtes, volume de données, rendu côté navigateur), puis corriger, par exemple par pagination, chargement différé ou virtualisation du rendu, avec des tests de charge.

### 9. Pas d'intégration GitLab : double saisie et risque de départ — Should
- **Justification** : Le thème est Should : il ne rentre pas dans le sprint, mais il rentre dans l'horizon Should. Son score est de 0,37, avec 2 demandeurs et un impact de 3, mais un effort de 13 points.
- **Point d'attention** : Il a le plus de relances de la liste (3) et un enjeu Rétention, avec un risque de départ évoqué dans le titre. Son score est faible surtout à cause de l'effort de 13 points, pas parce que l'enjeu serait mineur.
- *Impact* : Relevé d'un cran par rapport à la base Majeur : FB-013 évoque le non-renouvellement de 40 licences en janvier, FB-039 un renouvellement dans 6 semaines et FB-027 un test d'un concurrent, ce qui menace l'objectif de rétention de 92 % et l'adoption par les équipes techniques.
- *Confidence* : Le problème est clair et le risque business explicite, mais seuls deux clients (cinq messages) s'expriment, ce qui limite la certitude sur la taille réelle de la demande.
- *Effort* : Estimation reprise telle quelle du backlog.

### 10. Créer des dépendances entre tâches dans le Gantt est trop long — Could
- **Justification** : Le thème est Could : il est au-delà de la capacité des sprints à venir. Son score est de 0,23, avec 3 demandeurs et une gravité Majeure, mais un effort de 21 points.
- **Point d'attention** : Le Could vient surtout de l'effort de 21 points, pas d'un faible intérêt : 3 demandeurs, c'est plus que TH-4 ou TH-6. Aucune relance n'a eu lieu.
- *Impact* : Base Majeur conservée : la perte de temps est réelle sur les gros plannings (FB-004 : 200 tâches, FB-023 : plannings de chantier), mais une alternative existe via le panneau de détail et aucun enjeu de rétention n'est cité.
- *Confidence* : Le besoin est clair (créer une dépendance par glisser-déposer), mais seuls trois demandeurs l'expriment et FB-023 renvoie à un collègue, donc peut-être au même compte.
- *Effort* : Estimation reprise telle quelle du backlog.

### 11. Gérer les fiches de paie et les congés dans Orbiteam — Won't
- **Justification** : Le thème est Won't car il est hors vision produit (fiches de paie et congés). Sa gravité est Mineure, avec un seul demandeur.
- **Point d'attention** : Le score de 0,0 vient de l'absence d'impact et de confiance dans les données, pas d'une évaluation chiffrée. Le classement tient à la règle de vision produit.

### 12. Suivre ses prospects commerciaux directement dans Orbiteam — Won't
- **Justification** : Le thème est Won't car il est hors vision produit (suivi des prospects commerciaux). Sa gravité est Mineure, avec un seul demandeur.
- **Point d'attention** : Le score de 0,0 vient de l'absence d'impact et de confiance dans les données, pas d'une évaluation chiffrée. Le thème est nouveau, donc sa tendance n'est pas encore lisible.
