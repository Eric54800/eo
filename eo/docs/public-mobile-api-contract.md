# Contrat API Public Mobile-First

Reference technique pour l'application mobile publique anonyme.

Hypotheses produit:
- aucun compte public
- aucun login public
- consultation libre
- suivi des structures gere localement sur l'appareil
- les endpoints publics doivent rester lisibles, stables et sans donnees privees

## Statut

Ce document decrit:
- l'API publique deja disponible dans le backend
- le contrat recommande a stabiliser pour le mobile
- les ecarts connus entre l'etat actuel et la cible

## Principes

- format JSON
- endpoints en lecture seule
- aucune authentification requise
- le `slug` de structure est l'identifiant public fonctionnel
- seules les criées `published` sont exposees publiquement
- les pieces jointes et documents publics sont exposes uniquement via leurs URLs publiques

## Identifiant public de structure

- identifiant fonctionnel: `slug`
- exemple: `eo`
- usage:
  - page publique web: `/o/[slug]`
  - detail structure API: `/api/public/organisations/<slug>/`
  - filtrage publications: `/api/public/publications/?organisation_slug=<slug>`

Recommendation stable a conserver:
- ne jamais exposer un autre identifiant public principal cote mobile
- garder `slug` comme cle de navigation, partage et futur topic push

## Endpoints publics existants

### GET `/api/public/organisations/`

Usage:
- liste publique des structures
- utile pour la decouverte dans l'app mobile

Auth:
- aucune

Tri actuel:
- par `nom` croissant

Reponse:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 2,
      "nom": "EO",
      "slug": "eo",
      "adresse": "1 rue de test",
      "code_postal": "1000",
      "ville": "Bruville",
      "pays": "France",
      "presentation": "Presentation publique",
      "public_email": "contact@eo.test",
      "telephone": "+33 1 02 03 04 05",
      "public_cover_image_url": "http://127.0.0.1:8000/media/...",
      "public_avatar_image_url": "http://127.0.0.1:8000/media/...",
      "cover_position_x": 50,
      "cover_position_y": 50,
      "horaires": "Mardi 14h-18h",
      "public_documents": [
        {
          "id": 1,
          "file": "http://127.0.0.1:8000/media/...",
          "display_name": "Bulletin d'adhesion"
        }
      ],
      "subscription": {
        "status": "trialing",
        "trial_end": "2026-06-19T14:00:00Z",
        "current_period_end": null,
        "cancel_at_period_end": false,
        "cancel_at": null,
        "publication_access_active": true,
        "created_at": "2026-03-21T14:00:00Z",
        "updated_at": "2026-03-21T14:00:00Z"
      }
    }
  ]
}
```

Remarque:
- pour l'app publique, le bloc `subscription` n'est pas indispensable au MVP
- il peut rester expose si l'on accepte ce couplage, mais il ne doit pas etre utilise comme information produit publique

### GET `/api/public/organisations/<slug>/`

Usage:
- detail public d'une structure
- source principale pour l'ecran detail structure dans l'app

Auth:
- aucune

Lookup:
- `slug`

Reponse:

```json
{
  "id": 2,
  "nom": "EO",
  "slug": "eo",
  "adresse": "1 rue de test",
  "code_postal": "1000",
  "ville": "Bruville",
  "pays": "France",
  "presentation": "Presentation publique",
  "public_email": "contact@eo.test",
  "telephone": "+33 1 02 03 04 05",
  "public_cover_image_url": "http://127.0.0.1:8000/media/...",
  "public_avatar_image_url": "http://127.0.0.1:8000/media/...",
  "cover_position_x": 50,
  "cover_position_y": 50,
  "horaires": "Mardi 14h-18h",
  "public_documents": [
    {
      "id": 1,
      "file": "http://127.0.0.1:8000/media/...",
      "display_name": "Bulletin d'adhesion"
    }
  ],
  "subscription": {
    "status": "trialing",
    "trial_end": "2026-06-19T14:00:00Z",
    "current_period_end": null,
    "cancel_at_period_end": false,
    "cancel_at": null,
    "publication_access_active": true,
    "created_at": "2026-03-21T14:00:00Z",
    "updated_at": "2026-03-21T14:00:00Z"
  }
}
```

Comportement attendu:
- `200` si la structure existe
- `404` sinon

### GET `/api/public/publications/`

Usage:
- liste publique des criées publiees
- pour une structure donnee ou, plus tard, pour une agregation simple

Auth:
- aucune

Filtres supportes actuellement:
- `organisation_slug=<slug>`
- `organisation__slug=<slug>` (legacy, a considerer comme compatibilite)

Tri actuel:
- `-date_publication`, puis `-id`

Reponse:

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 10,
      "organisation": {
        "id": 2,
        "nom": "EO",
        "slug": "eo",
        "subscription": {
          "status": "trialing",
          "trial_end": "2026-06-19T14:00:00Z",
          "current_period_end": null,
          "cancel_at_period_end": false,
          "cancel_at": null,
          "publication_access_active": true,
          "created_at": "2026-03-21T14:00:00Z",
          "updated_at": "2026-03-21T14:00:00Z"
        }
      },
      "type": "information",
      "status": "published",
      "titre": "Test reprise",
      "contenu_preview": "Ceci est une criee de test...",
      "date_publication": "2026-03-21T14:00:00Z",
      "event_start": null,
      "event_end": null,
      "event_location": "",
      "attachments_count": 1,
      "attachments": [
        {
          "id": 3,
          "file": "http://127.0.0.1:8000/media/...",
          "display_name": "Programme"
        }
      ]
    }
  ]
}
```

Regles:
- seules les criées `published` sortent
- les brouillons et archives ne doivent jamais etre exposes ici

## Contrat recommande pour le MVP mobile

Pour le mobile, on recommande de considerer comme contractuels uniquement les champs ci-dessous.

### Structure publique

Champs a consommer:
- `id`
- `nom`
- `slug`
- `presentation`
- `adresse`
- `code_postal`
- `ville`
- `pays`
- `public_email`
- `telephone`
- `public_cover_image_url`
- `public_avatar_image_url`
- `cover_position_x`
- `cover_position_y`
- `horaires`
- `public_documents[]`
  - `id`
  - `file`
  - `display_name`

Champs a ne pas utiliser dans le mobile MVP:
- `subscription`

Recommendation:
- a terme, retirer `subscription` du contrat public mobile si aucun besoin public ne le justifie

### Criée publique

Champs a consommer:
- `id`
- `organisation.id`
- `organisation.nom`
- `organisation.slug`
- `type`
- `status`
- `titre`
- `contenu_preview`
- `date_publication`
- `event_start`
- `event_end`
- `event_location`
- `attachments_count`
- `attachments[]`
  - `id`
  - `file`
  - `display_name`

Champs manquants pour le mobile:
- le `contenu` complet n'est pas expose par la liste publique actuelle

Recommendation MVP:
- ajouter un endpoint detail public de criée

## Endpoint recommande a ajouter

### GET `/api/public/publications/<id>/`

Usage:
- detail d'une criée depuis le mobile

Auth:
- aucune

Regles:
- uniquement pour une criée `published`

Statut:
- implemente

Reponse cible:

```json
{
  "id": 10,
  "organisation": {
    "id": 2,
    "nom": "EO",
    "slug": "eo"
  },
  "type": "information",
  "status": "published",
  "titre": "Test reprise",
  "contenu": "Contenu complet de la criee",
  "date_publication": "2026-03-21T14:00:00Z",
  "event_start": null,
  "event_end": null,
  "event_location": "",
  "attachments": [
    {
      "id": 3,
      "file": "http://127.0.0.1:8000/media/...",
      "display_name": "Programme"
    }
  ]
}
```

## Regles de stabilite

A figer avant de coder l'app:
- conserver `slug` comme identifiant public de structure
- conserver `organisation_slug` comme filtre principal des publications
- conserver les URLs de medias en absolu ou definir une convention unique
- ne jamais exposer de brouillons cote public
- ne jamais introduire de dependance a l'auth publique

## Ecarts connus

### 1. Le detail de criée publique manque

Impact:
- l'app peut afficher une liste, mais pas un detail public riche sans reutiliser un endpoint prive

Action:
- creer `GET /api/public/publications/<id>/`

### 2. Le bloc `subscription` est expose publiquement

Impact:
- couplage inutile entre logique d'abonnement structure et surface publique

Action:
- ne pas le consommer dans l'app
- envisager sa suppression du contrat public plus tard

### 3. Le filtre legacy `organisation__slug` existe encore

Impact:
- deux manieres de faire la meme chose

Action:
- documenter `organisation_slug` comme seule cle publique
- garder `organisation__slug` uniquement pour compatibilite temporaire

## Topics push

Convention recommandee:
- `eo_org_<slug>`

Exemples:
- `eo_org_eo`
- `eo_org_association-test`

Usage futur:
- l'app suit une structure localement
- l'appareil s'abonne au topic correspondant
- le backend emet vers ce topic a la publication d'une criée

## Priorite immediate

Ordre recommande:
1. valider ce contrat
2. ajouter le detail public de criée
3. ajouter les tests backend API publique correspondants
4. seulement ensuite demarrer le squelette mobile

