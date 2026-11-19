# Prompt de génération du jeu de données

*Rédigé par l'humain, exécuté par l'IA. Conservé pour la traçabilité de la démarche.*

---

Génère le jeu de données de démonstration d'un agent IA qui assiste le Product Owner d'Orbiteam, un SaaS de gestion de projet fictif.

**1. Feedbacks (`feedbacks.json`) : 50 entrées, en français.**
- Canaux : email, ticket support, commentaire (in-app ou avis Play Store). Style réaliste propre à chaque canal : un ticket a un objet, un avis Play Store est court et parfois sans contexte.
- Champs : id (FB-001 à FB-050, dans l'ordre chronologique), canal, source, date, auteur, entreprise, objet, contenu. **Aucune étiquette** dans ce fichier : c'est à l'agent de classer.
- Période : 4 semaines, du 2026-10-20 au 2026-11-16. La période en cours pour le calcul des tendances est la dernière semaine (10 au 16 novembre).
- 9 problèmes récurrents, avec des formulations variées pour tester le regroupement :
  - export PDF du planning inexploitable (stable) ; FB-003 en fait partie ;
  - connexion SSO en échec depuis la mise en production web du 9 novembre (**nouveau**, 8 feedbacks concentrés sur la dernière semaine, symptômes différents : erreur SAML, déconnexions, message vague « je n'arrive plus à me connecter ») ;
  - crash de l'application Android depuis la v3.8 (**en hausse**) ;
  - intégration GitLab demandée, avec une menace de non-renouvellement qui monte en puissance (stable) ;
  - dépendances par glisser-déposer dans le Gantt (peu de demandes, cible restreinte) ; FB-004 en fait partie ;
  - trop de notifications email (**en baisse**, mais parce que les utilisateurs ont désactivé les notifications, pas parce que le problème est résolu) ;
  - synchronisation avec Google Agenda ;
  - lenteur du Kanban sur les gros projets ;
  - export détaillé des temps passés pour la facturation (une fonctionnalité existante est insuffisante).
- Pièges volontaires : questions de support non actionnables, remerciements, un spam, deux demandes hors vision (paie, CRM), un feedback qui mélange deux problèmes, un problème de mot de passe qui ressemble au problème SSO sans en faire partie, des feedbacks qui proposent une solution au lieu de décrire le problème.

**2. Backlog existant (`backlog.json`) : 12 éléments.** Certains correspondent aux problèmes ci-dessus, d'autres non. Les incidents SSO, crash Android et lenteur Kanban n'y figurent pas encore.

**3. Contexte produit (`contexte_produit.md`)** : vision, hors vision, objectifs du trimestre, capacité de l'équipe, mises en production récentes.

**4. Étiquettes de référence (`labels_attendus.json`)** : pour chaque feedback, thème(s), catégorie, gravité et enjeu business attendus, pour mesurer la précision de l'agent. Elles seront relues et validées par l'humain.
