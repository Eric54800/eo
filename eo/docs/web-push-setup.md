# Mise en service des alertes Web Push Éo

## Données transmises

Lorsqu'une source publie une criée, Éo transmet au service Push associé au
navigateur de chaque abonné actif :

- le titre de notification ;
- un aperçu limité à 120 caractères ;
- le lien interne vers la criée.

L'abonnement reste anonyme. Le backend conserve néanmoins le point de
terminaison Push, ses deux clés techniques et l'agent utilisateur. Ces éléments
doivent être mentionnés dans la politique de confidentialité avant ouverture au
public.

## Générer la paire VAPID

Depuis l'environnement Python du backend :

```bash
vapid --gen --applicationServerKey
```

La clé privée ne doit jamais être copiée dans le projet Next.js ni dans une
variable commençant par `NEXT_PUBLIC_`.

## Configuration backend

```text
WEB_PUSH_VAPID_PRIVATE_KEY=<clé privée ou chemin du fichier PEM>
WEB_PUSH_VAPID_SUBJECT=mailto:<adresse de contact du service>
WEB_PUSH_ENABLED=true
```

L'envoi reste désactivé tant que `WEB_PUSH_ENABLED` n'est pas explicitement à
`true` et que la clé privée n'est pas renseignée.

## Configuration du site

```text
NEXT_PUBLIC_WEB_PUSH_VAPID_PUBLIC_KEY=<applicationServerKey publique>
```

Après modification des variables du site, reconstruire le frontend. Sur iPhone,
les alertes ne peuvent être demandées que depuis la web-app ajoutée à l'écran
d'accueil.

## Ordre de mise en service

1. Appliquer les migrations Django `0016` et `0017`.
2. Configurer les clés VAPID sans activer l'envoi.
3. Déployer le backend et le site sur HTTPS.
4. Ajouter Éo à l'écran d'accueil d'un téléphone de test.
5. Suivre une source puis activer ses alertes.
6. Vérifier dans l'administration qu'un abonnement actif est enregistré.
7. Activer `WEB_PUSH_ENABLED=true`.
8. Publier une criée de test non sensible et vérifier sa réception.

## Retour arrière

Repasser `WEB_PUSH_ENABLED=false` arrête immédiatement les nouveaux envois sans
supprimer les abonnements existants. Le mécanisme de publication reste
fonctionnel même si un service Push est indisponible.
