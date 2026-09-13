# EO Stripe Setup

Preparation technique puis branchement du webhook de test Stripe.

## Variables backend

Configurer ces variables d'environnement pour le backend Django:

- `DJANGO_SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_ID`
- `STRIPE_SUCCESS_URL`
- `STRIPE_CANCEL_URL`

## Valeurs de dev recommandees

Exemple local:

```bash
export STRIPE_SECRET_KEY="sk_test_..."
export STRIPE_WEBHOOK_SECRET=""
export STRIPE_PRICE_ID="price_1T9MuzAKuv2Z6tKXgnznRbcu"
export STRIPE_SUCCESS_URL="http://127.0.0.1:3000/organisations/{slug}/administration?billing=success"
export STRIPE_CANCEL_URL="http://127.0.0.1:3000/organisations/{slug}/administration?billing=cancel"
```

Notes:

- le `price_id` de test actuellement cree dans Stripe pour EO est `price_1T9MuzAKuv2Z6tKXgnznRbcu`
- `STRIPE_WEBHOOK_SECRET` sera renseigne apres creation du webhook Stripe
- l'essai gratuit de 90 jours est envoye par EO au moment de creer la session Checkout

## Service backend

Le point d'entree Stripe est:

- `core/services/stripe_service.py`

Il centralise:

- creation checkout session
- creation customer portal session
- validation des webhooks

## Notes

- les endpoints billing backend sont deja en place:
  - `POST /api/billing/checkout-session/`
  - `POST /api/billing/customer-portal/`
  - `POST /api/billing/webhook/`
- Stripe ne devient la source de verite active qu'une fois le webhook de test relie
- l'admin Django `Subscription` reste utile pour supervision et support

## Tester sans payer en vrai

Stripe permet de tester tout le parcours en environnement de test:

- creation de la session Checkout
- abonnement mensuel
- retour succes / annulation
- webhook
- synchronisation locale de `Subscription`

Utiliser une carte de test Stripe, par exemple:

- `4242 4242 4242 4242`
- date future au choix
- CVC au choix
- code postal au choix

## Brancher le webhook de test Stripe

1. Verifier que Django tourne localement sur:

```bash
http://127.0.0.1:8000
```

2. Dans Stripe, rester en `Environnement de test`.

3. Ouvrir la section webhooks, puis ajouter un endpoint.

4. Renseigner cette URL:

```text
http://127.0.0.1:8000/api/billing/webhook/
```

5. Selectionner au minimum ces evenements:

- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.paid`
- `invoice.payment_failed`

6. Creer l'endpoint, puis copier le `Signing secret` qui ressemble a:

```text
whsec_...
```

7. Le renseigner dans l'environnement backend:

```bash
export STRIPE_WEBHOOK_SECRET="whsec_..."
```

8. Relancer Django.

## Parcours de test recommande

1. Ouvrir:

```text
http://127.0.0.1:3000/organisations/eo/administration
```

2. Cliquer sur le bouton d'abonnement.

3. Verifier que Stripe Checkout affiche:

- `10,00 EUR / mois`
- le produit `EO`
- l'essai gratuit de `90 jours`

4. Payer avec une carte de test Stripe.

5. Verifier le retour sur:

```text
/organisations/eo/administration?billing=success
```

6. Verifier ensuite que l'abonnement local est bien mis a jour:

- dans l'interface de la structure
- ou dans l'admin Django via `Subscription`

## Si le statut ne se met pas a jour

Verifier dans cet ordre:

1. `STRIPE_SECRET_KEY` est bien une cle de test valide
2. `STRIPE_PRICE_ID` vaut bien `price_1T9MuzAKuv2Z6tKXgnznRbcu`
3. `STRIPE_WEBHOOK_SECRET` est bien renseigne
4. le webhook Stripe pointe bien vers `/api/billing/webhook/`
5. Django tourne au moment du paiement
