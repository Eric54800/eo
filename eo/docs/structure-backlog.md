# EO Backlog Structure

Backlog dedie au parcours "structure", c'est-a-dire le parcours des organisations qui utilisent EO pour publier leurs criees.

Objectif:
- terminer le parcours structure avant d'ouvrir plus loin le chantier public mobile-first

## Phases

### Phase 1 - Onboarding structure
- creation de compte
- creation de structure
- premiere prise en main

### Phase 2 - Edition de la structure
- informations publiques
- visuel
- coherence entre admin et page publique

### Phase 3 - Gestion complete des criees
- creation
- edition
- archivage / suppression
- pilotage par structure

### Phase 4 - Membres et administration
- membres
- roles
- permissions

### Phase 5 - Finalisation du dashboard structure
- lisibilite
- abonnement
- tests critiques

## P0

### ST-01 - Finaliser le parcours de creation de compte structure
Surface:
- frontend Next.js
- backend Django

Objectif:
- permettre a une structure d'entrer dans EO sans bricolage

Taches:
- verifier l'existence du parcours de signup
- le rendre visible et coherent si necessaire
- verifier la redirection apres creation de compte

Critere d'acceptation:
- un nouveau compte structure peut etre cree et reutilise simplement

Dependances:
- aucune

### ST-02 - Finaliser la creation de structure
Surface:
- frontend Next.js
- backend Django

Objectif:
- rendre fiable `creer ma structure`

Taches:
- valider les champs minimaux
- corriger la gestion des erreurs
- corriger les cas de doublons
- verifier la redirection vers `/organisations/[slug]`

Critere d'acceptation:
- une structure peut etre creee sans ambiguite ni etat casse

Dependances:
- ST-01

### ST-03 - Ajouter un premier parcours guide apres creation
Surface:
- frontend Next.js

Objectif:
- aider la structure a savoir quoi faire ensuite

Taches:
- apres creation:
  - completer la page
  - publier une premiere criee
  - voir la page publique

Critere d'acceptation:
- apres creation, le prochain pas est evident

Dependances:
- ST-02

### ST-04 - Ajouter l'edition complete de la structure
Surface:
- frontend Next.js
- backend Django

Objectif:
- permettre a une structure de completer sa page publique

Taches:
- edition de:
  - nom
  - presentation
  - email public
  - telephone
  - adresse
  - ville
  - pays

Critere d'acceptation:
- les informations publiques d'une structure sont modifiables depuis l'admin

Dependances:
- ST-02

### ST-05 - Ajouter la gestion du visuel public
Surface:
- frontend Next.js
- backend Django

Objectif:
- permettre a une structure d'avoir une identite visuelle minimale

Taches:
- image ou visuel public
- rendu coherent sur dashboard et page publique

Critere d'acceptation:
- la structure peut definir un visuel public et le voir cote admin/public

Dependances:
- ST-04

### ST-06 - Ajouter un apercu clair de la page publique
Surface:
- frontend Next.js

Objectif:
- rendre le lien entre espace structure et page publique immediat

Taches:
- lien public visible
- bouton d'ouverture
- resume des informations publiques et des criees visibles

Critere d'acceptation:
- une structure comprend tout de suite ce qui est visible publiquement

Dependances:
- ST-04
- ST-05

### ST-07 - Consolider la creation de criee
Surface:
- frontend Next.js
- backend Django

Objectif:
- finaliser la creation info/evenement

Taches:
- revoir validations
- revoir messages d'erreur
- verifier retour vers la structure
- verifier coherence avec la page publique

Critere d'acceptation:
- le formulaire de publication est stable et comprehensible

Dependances:
- aucune

### ST-08 - Ajouter l'edition d'une criee
Surface:
- frontend Next.js
- backend Django

Objectif:
- permettre de corriger une criée deja creee

Taches:
- formulaire d'edition
- pre-remplissage des champs
- update titre / contenu / statut / dates / lieu
- retour propre apres sauvegarde

Critere d'acceptation:
- une criée existante peut etre modifiee depuis l'admin

Dependances:
- ST-07

### ST-09 - Ajouter archivage ou suppression d'une criee
Surface:
- frontend Next.js
- backend Django

Objectif:
- donner un vrai cycle de vie aux criées

Taches:
- action archiver
- suppression si conservee
- protection UX minimale

Critere d'acceptation:
- une structure peut retirer proprement une criée de la circulation

Dependances:
- ST-08

### ST-10 - Ajouter une meilleure vue liste des criees
Surface:
- frontend Next.js

Objectif:
- piloter les criées plus facilement

Taches:
- filtrer par structure courante si necessaire
- distinguer brouillons / publiees / archivees
- acces plus rapide au detail

Critere d'acceptation:
- la liste des criées devient un vrai outil de gestion

Dependances:
- ST-08

## P1

### ST-11 - Finaliser la gestion des membres
Surface:
- frontend Next.js
- backend Django

Objectif:
- permettre l'administration de la structure a plusieurs

Taches:
- liste membres
- invitation
- affichage du role

Critere d'acceptation:
- un owner/admin peut gerer les membres de sa structure

Dependances:
- aucune

### ST-12 - Permettre le changement de role
Surface:
- frontend Next.js
- backend Django

Objectif:
- administrer correctement la gouvernance de la structure

Taches:
- changer owner/admin/member selon regles autorisees
- proteger les cas sensibles

Critere d'acceptation:
- les roles sont modifiables de facon controlee

Dependances:
- ST-11

### ST-13 - Verrouiller les permissions du parcours structure
Surface:
- backend Django

Objectif:
- eviter toute fuite ou action non autorisee

Taches:
- verifier:
  - edition structure
  - publications
  - pieces jointes
  - membres

Critere d'acceptation:
- les permissions structure sont coherentes et testables

Dependances:
- ST-11

### ST-14 - Clarifier l'abonnement structure dans le dashboard
Surface:
- frontend Next.js

Objectif:
- rendre lisible l'etat commercial de la structure

Taches:
- etat essai / actif / resilie
- date de fin d'essai
- message clair

Critere d'acceptation:
- une structure comprend son statut d'abonnement au premier regard

Dependances:
- aucune

## P2

### ST-15 - Rendre le dashboard structure pleinement coherent
Surface:
- frontend Next.js

Objectif:
- finaliser l'espace principal de la structure

Taches:
- conforter la hierarchie actuelle
- clarifier les blocs administration
- garder l'action principale sur la publication

Critere d'acceptation:
- le dashboard structure est stable, lisible et orienté action

Dependances:
- ST-06
- ST-10
- ST-14

### ST-16 - Ajouter les tests critiques du parcours structure
Surface:
- backend Django
- frontend Next.js

Objectif:
- verrouiller le parcours structure contre les regressions

Taches:
- login
- creation structure
- publication
- rendu public
- membres si possible

Critere d'acceptation:
- les regressions critiques du parcours structure sont detectees automatiquement

Dependances:
- ST-02
- ST-07
- ST-11

## Ordre recommande d'execution

1. ST-02
2. ST-04
3. ST-05
4. ST-06
5. ST-07
6. ST-08
7. ST-09
8. ST-10
9. ST-11
10. ST-12
11. ST-13
12. ST-14
13. ST-15
14. ST-16
