# EO Backlog Mobile

Backlog mobile re-priorise apres validation du socle sur iPhone.

Contexte produit:
- public totalement anonyme
- aucun compte public
- aucun login public
- suivi des structures stocke localement sur l'appareil
- web public = support, partage, point d'entree vers l'app
- la valeur mobile depend d'abord de l'experience, puis des notifications

## Etat actuel

Deja en place:
- API publique stable pour la liste des structures
- detail public de structure
- liste publique des criées par structure
- detail public d'une criée
- app Expo mobile fonctionnelle sur iPhone
- suivi local des structures
- fil agrege des criées des structures suivies
- logique du fil orientee usage:
  - evenements a venir d'abord
  - evenements passes masques apres le lendemain
  - informations masquables localement
- preferences locales de notifications par source
- convention de topic documentee: `eo_org_<slug>`
- backend de diffusion pose avec `NotificationDispatch`
- home mobile recentree sur les criées
- recherche locale de source
- navigation mobile `Criées / Sources / Trouver`
- detail complet de criée dans l'app
- retours de navigation plus naturels
- suivre une source active implicitement les alertes si iPhone l'autorise

Pas encore finalise:
- detail source vraiment abouti
- design mobile plus intentionnel et plus leger
- terme public definitif pour remplacer partout `structure`
- push reel jusqu'au telephone
- deep links web <-> mobile
- affinage des cartes de criées et des etats vides
- envoi push reel jusqu'au telephone

## Priorites

### P0 - Consolider le coeur mobile

#### EO-M01 - Refonte visuelle mobile
Surface:
- application mobile

Objectif:
- transformer le prototype fonctionnel en une vraie experience mobile Eo

Taches:
- integrer une hero mobile qui porte la marque Eo
- revoir typographie, espacements, couleurs et cartes
- donner plus de place aux structures suivies
- rendre le fil des criées plus lisible
- retravailler l'ecran detail structure

Statut:
- largement avance

Dependances:
- aucune

#### EO-M02 - Ajouter la recherche de structure
Surface:
- application mobile

Objectif:
- permettre de trouver rapidement une structure par son nom

Taches:
- ajouter un champ de recherche
- filtrer localement la liste des structures chargees
- gerer les etats vide / aucun resultat
- conserver un comportement fluide sur iPhone

Statut:
- fait en local sur l'app

Dependances:
- aucune

#### EO-M03 - Clarifier la navigation mobile
Surface:
- application mobile

Objectif:
- rendre les ecrans plus naturels a utiliser sur telephone

Taches:
- mieux separer:
  - accueil
  - structures suivies
  - fil
  - decouverte
- ajouter des retours et transitions plus clairs
- simplifier les actions sur les cartes

Statut:
- fait pour le socle mobile actuel

Dependances:
- EO-M01

#### EO-M04 - Ajouter un vrai detail de criée dans l'app
Surface:
- application mobile

Objectif:
- permettre de lire une criée complete depuis le fil ou depuis une structure

Taches:
- ajouter l'ecran detail criée
- afficher:
  - titre
  - contenu complet
  - type
  - date
  - informations evenement
  - pieces jointes
- ouvrir le detail depuis le fil et depuis la structure

Statut:
- fait

Dependances:
- endpoint detail public deja disponible

#### EO-M05 - Faire une vraie fiche source mobile
Surface:
- application mobile

Objectif:
- rendre la fiche source utile, legere et immediate a comprendre

Taches:
- remplacer les derniers textes trop administratifs
- mieux presenter:
  - presentation
  - contact
  - horaires
  - documents
- simplifier encore l'action de suivi
- rendre l'identite de la source plus visible

Critere d'acceptation:
- la fiche source aide a comprendre qui publie et comment le joindre

Dependances:
- EO-M01
- EO-M03

#### EO-M06 - Revoir le vocabulaire public
Surface:
- application mobile
- web public ensuite

Objectif:
- sortir du terme `structure` quand il est incomprehensible pour le grand public

Taches:
- fixer le vocabulaire principal:
  - `source`
  - `qui publie`
  - `criée`
- harmoniser les ecrans mobile
- preparer l'alignement futur avec le web public

Critere d'acceptation:
- les mots utilises sont naturels pour un public non interne

Dependances:
- aucune

### P1 - Finir le produit mobile avant le push reel

#### EO-M07 - Renforcer le suivi local des sources
Surface:
- application mobile

Objectif:
- rendre le suivi plus explicite et plus robuste

Taches:
- mieux mettre en avant les structures suivies
- ajouter des etats vides plus utiles
- permettre un acces plus direct a une structure suivie
- verifier le comportement apres fermeture et reouverture de l'app

Critere d'acceptation:
- le suivi local est comprehensible et fiable

Dependances:
- EO-M03

#### EO-M08 - Ajuster les cartes de criées
Surface:
- application mobile

Objectif:
- rendre le fil plus utile au quotidien sans l'encombrer

Taches:
- mieux distinguer evenement et information
- clarifier encore les dates
- verifier la densite visuelle sur iPhone
- revoir les etats vides du fil

Critere d'acceptation:
- les cartes de criées sont lisibles en un coup d'oeil

Dependances:
- EO-M04

#### EO-M09 - Ajuster la fiche source
Surface:
- application mobile

Objectif:
- mieux mettre en avant l'identite et les informations utiles d'une structure

Taches:
- mieux exploiter couverture et avatar
- mieux afficher presentation, contact, horaires, documents
- mieux distinguer actions:
  - suivre
  - activer les notifications
  - consulter les criées

Critere d'acceptation:
- la fiche structure ressemble a une vraie page publique mobile Eo

Dependances:
- EO-M01

### P2 - Brancher les notifications reelles

#### EO-M10 - Brancher un vrai fournisseur push
Surface:
- backend Django
- application mobile

Objectif:
- envoyer une notification reelle jusqu'au telephone

Taches:
- choisir le fournisseur V1
- brancher le service backend de diffusion a ce fournisseur
- envoyer les donnees minimales:
  - titre
  - message
  - organisation_slug
  - publication_id

Critere d'acceptation:
- publier une criée peut produire une notification visible sur un appareil de test

Dependances:
- backend de diffusion deja pose

#### EO-M11 - Relier les preferences locales au vrai canal push
Surface:
- application mobile
- backend Django

Objectif:
- faire correspondre les toggles de notification de l'app a un canal de diffusion reel

Taches:
- brancher l'activation des notifications a l'abonnement reel
- brancher la desactivation
- garder le fonctionnement anonyme

Critere d'acceptation:
- activer les notifications pour une structure permet de recevoir sa prochaine criée

Dependances:
- EO-M10

#### EO-M12 - Tester les scenarios push critiques
Surface:
- backend Django
- application mobile

Objectif:
- verifier que le systeme de notification est fiable pour le MVP

Taches:
- test de permission iPhone
- test activation / desactivation
- test reception sur criée publiee
- test ouverture de la bonne destination apres notification

Critere d'acceptation:
- les notifications sont exploitables pour un usage reel de demonstration

Dependances:
- EO-M11

### P3 - Ouvrir le web vers le mobile

#### EO-M13 - Adapter `/o/[slug]` comme porte d'entree vers l'app
Surface:
- frontend Next.js

Objectif:
- transformer la page publique web en passerelle naturelle vers l'app mobile

Taches:
- ajouter un CTA `Ouvrir dans l'app`
- ajouter un CTA `Suivre sur mobile`
- clarifier la promesse mobile

Critere d'acceptation:
- une structure publique pousse proprement vers l'app

Dependances:
- EO-M01

#### EO-M14 - Ajouter les deep links structure et criée
Surface:
- frontend Next.js
- application mobile

Objectif:
- ouvrir la bonne destination mobile depuis le web ou une notification

Taches:
- deep link structure
- deep link criée
- fallback web si l'app n'est pas disponible

Critere d'acceptation:
- une structure ou une criée s'ouvre directement au bon endroit dans l'app

Dependances:
- EO-M04
- EO-M13

#### EO-M15 - Orienter vers le site pour publier
Surface:
- application mobile
- frontend Next.js

Objectif:
- rediriger proprement vers le site web toute personne qui veut creer une source ou publier des criées

Taches:
- ajouter un point d'entree clair dans l'app:
  - `Publier une criée`
  - ou `Créer votre source`
- ouvrir la bonne page web depuis l'app
- expliquer simplement que la creation et l'administration se font sur le site
- placer ce renvoi au bon endroit:
  - ecran `Trouver`
  - fiche source
  - ou ecran d'information dedie

Critere d'acceptation:
- un utilisateur mobile comprend facilement que la publication se gere sur le site web et peut y acceder en un geste

Dependances:
- aucune

#### EO-M16 - Donner acces aux informations legales
Surface:
- application mobile
- frontend Next.js

Objectif:
- rendre accessibles depuis l'app les informations legales et de confiance

Taches:
- ajouter un point d'entree discret mais clair dans l'app
- ouvrir les pages web du site pour:
  - mentions legales
  - politique de confidentialite
  - CGU si disponibles
- verifier que ces liens restent faciles a trouver
- prevoir aussi un lien `A propos`

Critere d'acceptation:
- un utilisateur mobile peut acceder simplement aux pages legales du service depuis l'app

Dependances:
- aucune

## Ordre recommande maintenant

1. EO-M05 - Faire une vraie fiche source mobile
2. EO-M06 - Revoir le vocabulaire public
3. EO-M08 - Ajuster les cartes de criées
4. EO-M07 - Renforcer le suivi local des sources
5. EO-M15 - Orienter vers le site pour publier
6. EO-M16 - Donner acces aux informations legales
7. EO-M10 - Fournisseur push reel
8. EO-M11 - Liaison preferences locales / push
9. EO-M12 - Tests push
10. EO-M13 - CTA web vers mobile
11. EO-M14 - Deep links

## Decision produit recommandee

Avant de brancher les notifications reelles, il vaut mieux:
- finaliser la fiche source
- fixer le vocabulaire public
- finir d'alleger les cartes de criées

Autrement dit:
- priorite immediate = lisibilite produit + fiche source
- priorite suivante = push reel
