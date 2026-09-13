# EO Backlog Stripe

Backlog dedie a la mise en place de la facturation Stripe pour les structures.

Modele commercial fige:
- 1 plan unique
- 10 EUR par mois
- 1 structure = 1 abonnement
- essai gratuit de 3 mois
- resiliation a fin de periode
- a expiration:
  - admin accessible
  - page publique visible
  - publication bloquee

Principe d'architecture:
- Stripe devient la source de verite pour la facturation
- Django conserve la logique metier locale dans `Subscription`
- l'admin Django sert a la supervision et au support, pas a la gestion normale du paiement

## Phases

### Phase 1 - Preparer le socle Stripe
- config backend
- service Stripe dedie
- mapping local `Subscription`

### Phase 2 - Brancher le paiement
- creation checkout session
- retour vers EO
- liaison avec la structure

### Phase 3 - Synchroniser Stripe vers EO
- webhooks
- mapping statuts
- mise a jour automatique de `Subscription`

### Phase 4 - Finaliser l'UX structure
- CTA admin
- messages d'etat
- portail client Stripe

## P0

### BILL-01 - Ajouter la configuration Stripe au backend
Surface:
- backend Django
- configuration environnement

Objectif:
- preparer le projet a parler a Stripe sans brancher encore la logique metier

Taches:
- ajouter les variables d'environnement:
  - `STRIPE_SECRET_KEY`
  - `STRIPE_WEBHOOK_SECRET`
  - `STRIPE_PRICE_ID`
  - `STRIPE_SUCCESS_URL`
  - `STRIPE_CANCEL_URL`
- documenter leur role
- definir des valeurs de dev coherentes

Critere d'acceptation:
- le backend peut demarrer avec une configuration Stripe explicite

Dependances:
- aucune

### BILL-02 - Creer un service Stripe dedie
Surface:
- backend Django

Objectif:
- eviter de disperser la logique Stripe dans les views

Taches:
- creer un service `billing/stripe_service.py` ou equivalent
- centraliser:
  - creation checkout session
  - creation portal session
  - validation webhook
- preparer les helpers de mapping des objets Stripe

Critere d'acceptation:
- les appels Stripe passent par un service unique et lisible

Dependances:
- BILL-01

### BILL-03 - Ajouter `POST /api/billing/checkout-session/`
Surface:
- backend Django
- frontend Next.js

Objectif:
- permettre a une structure de demarrer son abonnement

Taches:
- endpoint authentifie
- recuperer la structure courante
- creer une checkout session Stripe
- injecter des metadonnees:
  - `organisation_id`
  - `organisation_slug`

Critere d'acceptation:
- une structure peut ouvrir une session Stripe Checkout a partir de son espace

Dependances:
- BILL-02

### BILL-04 - Ajouter `POST /api/billing/webhook/`
Surface:
- backend Django

Objectif:
- synchroniser automatiquement Stripe et EO

Taches:
- endpoint public
- verification de signature Stripe
- parser les evenements utiles
- journaliser les evenements non geres

Critere d'acceptation:
- le backend recoit et valide les webhooks Stripe

Dependances:
- BILL-02

### BILL-05 - Mapper `checkout.session.completed`
Surface:
- backend Django

Objectif:
- lier la session Stripe a la bonne structure

Taches:
- recuperer le `customer`
- recuperer la `subscription`
- retrouver `organisation_id` via metadata
- preparer ou aligner `Subscription`

Critere d'acceptation:
- une souscription Stripe aboutie est reliee a la structure EO correcte

Dependances:
- BILL-03
- BILL-04

### BILL-06 - Mapper `customer.subscription.created` et `updated`
Surface:
- backend Django

Objectif:
- faire de Stripe la source de verite des statuts

Taches:
- remplir / synchroniser:
  - `stripe_customer_id`
  - `stripe_subscription_id`
  - `status`
  - `trial_end`
  - `current_period_end`
- convertir les statuts Stripe vers:
  - `trialing`
  - `active`
  - `canceled`

Critere d'acceptation:
- un changement Stripe met a jour correctement `Subscription`

Dependances:
- BILL-04

### BILL-07 - Brancher les regles de publication sur les statuts Stripe
Surface:
- backend Django

Objectif:
- garantir la coherence produit avec la facturation

Taches:
- verifier que les regles locales correspondent au modele fige:
  - trialing autorise jusqu'a `trial_end`
  - active autorise jusqu'a `current_period_end`
  - canceled autorise jusqu'a `current_period_end`
  - sinon publication bloquee
- couvrir ces transitions par des tests

Critere d'acceptation:
- le droit de publier suit strictement l'etat d'abonnement

Dependances:
- BILL-06

## P1

### BILL-08 - Ajouter les CTA d'abonnement dans l'espace structure
Surface:
- frontend Next.js

Objectif:
- rendre l'abonnement activable depuis l'interface structure

Taches:
- ajouter `S'abonner`
- ajouter `Gerer mon abonnement`
- retirer le mode manuel temporaire de l'UI normale

Critere d'acceptation:
- une structure comprend comment s'abonner et gerer son abonnement

Dependances:
- BILL-03
- BILL-06

### BILL-09 - Ajouter `POST /api/billing/customer-portal/`
Surface:
- backend Django
- frontend Next.js

Objectif:
- deleguer a Stripe la gestion du moyen de paiement et de la resiliation

Taches:
- creer une session portail Stripe
- rediriger la structure depuis l'admin EO

Critere d'acceptation:
- une structure peut ouvrir le portail Stripe depuis EO

Dependances:
- BILL-02
- BILL-06

### BILL-10 - Mapper `customer.subscription.deleted`
Surface:
- backend Django

Objectif:
- gerer la fin effective d'un abonnement

Taches:
- marquer l'abonnement comme `canceled`
- mettre a jour la fin de periode si necessaire
- conserver la coherence de publication

Critere d'acceptation:
- une suppression d'abonnement cote Stripe est correctement repercutee dans EO

Dependances:
- BILL-04

### BILL-11 - Mapper `invoice.paid` et `invoice.payment_failed`
Surface:
- backend Django

Objectif:
- fiabiliser le suivi de vie d'un abonnement

Taches:
- journaliser le succes de paiement
- journaliser l'echec de paiement
- preparer une logique de support ou d'alerte simple

Critere d'acceptation:
- les paiements utiles sont visibles et exploitables cote projet

Dependances:
- BILL-04

## P2

### BILL-12 - Exposer proprement la supervision abonnement dans l'admin Django
Surface:
- admin Django

Objectif:
- te donner un cockpit projet utile, meme une fois Stripe branche

Taches:
- verifier les champs visibles
- verifier les filtres et recherches
- verifier les liens vers organisation / ids Stripe
- limiter l'usage a la supervision et au support

Critere d'acceptation:
- l'admin Django permet de comprendre rapidement l'etat commercial d'une structure

Dependances:
- BILL-06

### BILL-13 - Documenter l'exploitation Stripe locale et production
Surface:
- documentation

Objectif:
- rendre l'integration testable et maintenable

Taches:
- documenter:
  - configuration environnement
  - lancement local
  - ecoute webhook locale
  - procedure de test
  - points de controle

Critere d'acceptation:
- l'integration Stripe peut etre relancee sans memoire implicite

Dependances:
- BILL-01

## Ordre recommande

1. BILL-01
2. BILL-02
3. BILL-03
4. BILL-04
5. BILL-05
6. BILL-06
7. BILL-07
8. BILL-08
9. BILL-09
10. BILL-10
11. BILL-11
12. BILL-12
13. BILL-13

## Notes

Le minimum utile pour une V1 Stripe est:
- checkout session
- webhook
- synchronisation `Subscription`
- CTA admin structure

Le portail client Stripe peut venir juste apres, mais n'est pas le premier blocant.
