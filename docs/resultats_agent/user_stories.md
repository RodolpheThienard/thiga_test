# User Stories rédigées par l'agent

## US-001 · Rouvrir sans plantage les tâches avec pièces jointes sur l'application Android

*Problème : L'application Android plante à l'ouverture d'une tâche avec pièces jointes — Must, score RICE 4.0*

En tant qu'utilisateur de l'application Android Orbiteam (par exemple sur Samsung ou Android 14) qui consulte sur mobile des tâches contenant une photo ou une pièce jointe, je veux ouvrir ces tâches sans que l'application se ferme, afin de continuer à suivre mon travail depuis mon téléphone sans devoir passer par le navigateur mobile.

### Critères d'acceptation

```gherkin
Scénario: Ouverture d'une tâche avec une photo jointe
  Étant donné un utilisateur connecté à l'application Android Orbiteam v3.8 ou une version corrective
  Et une tâche contenant une photo en pièce jointe
  Quand l'utilisateur ouvre cette tâche
  Alors la fiche de la tâche s'affiche avec la photo visible dans la visionneuse de pièces jointes
  Et l'application ne se ferme pas
  Et la fiche est affichée en moins de 3 secondes sur une connexion Wi-Fi standard
```

```gherkin
Scénario: Ouverture d'une tâche avec une pièce jointe de type document
  Étant donné une tâche contenant une pièce jointe de type document (par exemple un PDF)
  Quand l'utilisateur ouvre la tâche puis ouvre la pièce jointe dans la visionneuse
  Alors le contenu s'affiche, ou une proposition d'ouverture dans une application externe est faite si le format n'est pas géré par la visionneuse
  Et l'application ne se ferme pas
```

```gherkin
Scénario: Ouverture d'une tâche sans pièce jointe
  Étant donné une tâche ne contenant aucune pièce jointe
  Quand l'utilisateur ouvre cette tâche
  Alors la fiche de la tâche s'affiche normalement
  Et l'application ne se ferme pas
```

```gherkin
Scénario: Ouverture d'une tâche avec 10 pièces jointes dont un fichier de 20 Mo
  Étant donné une tâche contenant 10 pièces jointes, dont un fichier de 20 Mo
  Quand l'utilisateur ouvre cette tâche puis fait défiler toutes les pièces jointes
  Alors la fiche s'affiche et toutes les pièces jointes sont accessibles
  Et l'application ne se ferme pas à aucun moment
```

```gherkin
Scénario: Pièce jointe corrompue, supprimée ou indisponible faute de réseau
  Étant donné une tâche dont une pièce jointe est corrompue, supprimée côté serveur ou impossible à charger faute de connexion
  Quand l'utilisateur ouvre la tâche puis tente d'afficher cette pièce jointe
  Alors un message d'erreur explicite s'affiche à la place de la pièce jointe
  Et le reste de la fiche (titre, description, statut, commentaires) reste consultable
  Et l'application ne se ferme pas
```

```gherkin
Scénario: Campagne de test sur les configurations remontées
  Étant donné un appareil Samsung sous Android 14 et au moins un autre appareil Android d'un fabricant différent
  Quand la QA ouvre 20 tâches avec photo ou pièce jointe sur chaque appareil
  Alors aucun plantage n'est constaté sur les 20 ouvertures de chaque appareil
```

**Complexité** : 5 story points.

**Hypothèses** : Hypothèses : (1) le plantage est localisé dans la nouvelle visionneuse de pièces jointes introduite en v3.8 (cohérent avec la date des retours, mais à confirmer par l'analyse des traces de crash) ; (2) la cause est reproductible en local sur Android 14 ; (3) le correctif ne demande pas de refonte de la visionneuse ; (4) une publication corrective sur les stores est possible sans retard particulier. L'estimation inclut le diagnostic, le correctif, les tests automatisés ou manuels sur plusieurs appareils, ainsi que la préparation de la publication corrective.

**Écart avec l'effort RICE** : L'effort RICE est de 3 points ; nous estimons 5 points. Le RICE suppose probablement un correctif ponctuel, alors que la cause racine n'est pas encore identifiée (une seule version, plusieurs appareils et pièces jointes de types variés). Nous ajoutons aussi le temps de QA sur plusieurs appareils et la publication corrective. Si le diagnostic montre une cause simple, par exemple un cas non géré dans la visionneuse, 3 points redeviennent réalistes.

**Questions ouvertes** :
- Disposons-nous des rapports de crash (outil de suivi des plantages) pour identifier la cause racine et le périmètre exact (versions d'Android, fabricants, types de fichiers) ?
- FB-037 ne mentionne pas de pièce jointe : le plantage touche-t-il aussi des tâches sans pièce jointe ? Cela changerait le périmètre et l'estimation.
- Le plantage est-il systématique pour toute pièce jointe ou seulement pour certains types, tailles ou sources (photo prise depuis l'appli, import, GitHub) ?
- Une publication corrective hors sprint est-elle possible, sans attendre le sprint du 2026-11-18 ? L'incident est bloquant depuis le 2026-11-07, donc l'objectif T4 « aucun incident bloquant non résolu sous 48 h » est déjà dépassé.
- Un retour arrière vers la v3.7 ou la désactivation de la nouvelle visionneuse (si elle est pilotable à distance) est-il envisageable comme mesure d'attente ?
- Quelle est la version minimale d'Android supportée et quelle matrice d'appareils la QA doit-elle couvrir ?
- Quelle communication prévoir envers les clients touchés, notamment ceux qui sont passés au navigateur mobile (FB-037) ?
- Combien d'utilisateurs actifs sont concernés, et des comptes Business ou Enterprise sont-ils à risque de non-renouvellement ?
- Le plantage existe-t-il aussi sur iOS ou est-il propre à Android ? Les retours reçus ne concernent qu'Android.

**Hors périmètre** :
- Refonte ou nouvelles fonctionnalités de la visionneuse de pièces jointes (annotation, zoom avancé, partage).
- Vérification de l'application iOS et de l'application web, sauf si l'analyse montre une cause commune.
- Mise en place d'un nouvel outil de suivi des plantages ou d'une stratégie générale de tests de non-régression mobile.
- Changement des formats ou des tailles maximales de pièces jointes acceptés.
- Rédaction et envoi de la communication client (traité par l'équipe support ou produit).
