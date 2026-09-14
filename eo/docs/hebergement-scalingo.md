# Éo — préparation du futur hébergement

État vérifié le 14 septembre 2026. Ce document prépare un déploiement futur ; il ne constitue ni un déploiement, ni une souscription, ni une modification DNS.

## Décision d'architecture

- Cible principale : Scalingo, région Paris (`osc-fr1`).
- Repli : Clever Cloud, région Paris.
- Backend : dépôt GitHub `eo` vers une application Django Scalingo.
- Base : PostgreSQL managé Scalingo, attaché au backend.
- Médias : stockage objet S3 en France, avec préférence actuelle pour OVHcloud.
- Frontend : dépôt GitHub `eo-web` vers une application Node.js/Next.js Scalingo.
- Domaine : `nange.fr` reste géré chez OVH ; le frontend et l'API utiliseront deux noms distincts.

```text
GitHub eo      -> Scalingo Django / Paris -> Scalingo PostgreSQL / Paris
                                           -> S3 compatible / France
GitHub eo-web  -> Scalingo Next.js / Paris
OVH            -> DNS nange.fr (modification uniquement au lancement)
```

## État technique constaté

### Backend

- Python 3.12 et Django 5.2 LTS.
- SQLite et stockage de médias local par défaut.
- PostgreSQL activable par `DATABASE_URL`, avec `psycopg` déjà déclaré.
- Modèles Django standards ; `JSONField`, `ImageField` et `FileField` sont compatibles PostgreSQL. Aucune migration manquante lors de l'audit.
- Web Push synchrone, sans worker ni ordonnanceur distinct identifié.
- Aucun paquet CORS n'est nécessaire dans l'architecture cible : le navigateur appelle le proxy Next.js sur la même origine, et Next.js communique avec Django côté serveur.

### Frontend

- Next.js 14.2, React 18 ; Node.js 22 est épinglé pour le futur runtime Scalingo.
- PWA avec manifeste, service worker et interface Web Push.
- Le serveur Node est obligatoire : routes API, cookies lus côté serveur, rendu dynamique et proxy vers Django. Un export intégralement statique n'est pas possible sans refonte.
- `BACKEND_URL` est la variable serveur à employer en préproduction et production. `NEXT_PUBLIC_API_BASE` reste disponible pour la compatibilité locale, mais ne doit contenir aucun secret.

## Variables futures du backend

Valeurs fictives uniquement : voir `.env.example`.

- `DJANGO_SECRET_KEY` : secret long et unique ; obligatoire si `DEBUG=false`.
- `DEBUG=false`.
- `ALLOWED_HOSTS=api.exemple.nange.fr,nom-app.osc-fr1.scalingo.io`.
- `CSRF_TRUSTED_ORIGINS=https://api.exemple.nange.fr,https://exemple.nange.fr`.
- `DATABASE_URL` : fournie automatiquement par l'add-on PostgreSQL Scalingo.
- `SECURE_SSL_REDIRECT=true` ; conserver `SECURE_HSTS_SECONDS=0` au premier lancement, puis activer HSTS seulement après validation complète de HTTPS et des domaines.
- Stripe et Web Push : conserver les fonctions désactivées tant que leurs clés réelles ne sont pas volontairement configurées.

### Stockage média S3

Le disque local reste utilisé lorsque `USE_S3_STORAGE=false`. Pour un futur bucket compatible S3 :

- `USE_S3_STORAGE=true`
- `S3_ENDPOINT_URL`
- `S3_BUCKET_NAME`
- `S3_REGION_NAME`
- `S3_ACCESS_KEY_ID`
- `S3_SECRET_ACCESS_KEY`
- `S3_CUSTOM_DOMAIN` (facultatif)
- `S3_QUERYSTRING_AUTH=true` pour des URLs signées, à reconsidérer selon la politique publique/privée retenue pour chaque type de média.

L'endpoint et la région doivent provenir du fournisseur au moment de créer le bucket. Aucun bucket ni identifiant n'est créé pendant cette préparation.

## Variables futures du frontend

- `BACKEND_URL=https://api.exemple.nange.fr` : URL interne au runtime Next.js.
- `NEXT_PUBLIC_WEB_PUSH_VAPID_PUBLIC_KEY` : clé publique seulement.
- `NEXT_PUBLIC_API_BASE` : facultative si toutes les communications navigateur restent relatives au frontend.

## Commandes prévues par les dépôts

- Backend : le `Procfile` démarre Gunicorn sur le port fourni par Scalingo.
- Frontend : Scalingo installe avec `npm ci`, exécute `npm run build`, puis utilise `npm start`.
- Les migrations doivent être exécutées dans une étape de lancement contrôlée après sauvegarde. Elles ne sont pas automatisées ici pour éviter qu'une mauvaise configuration future modifie une base au déploiement.
- Les statiques Django sont collectées dans `staticfiles/` et servies par WhiteNoise. Les médias utilisateurs ne doivent jamais dépendre du disque éphémère du PaaS.

## Migration future des données

1. Geler temporairement les écritures du prototype.
2. Sauvegarder ensemble `db.sqlite3` et `media/`, puis vérifier la sauvegarde.
3. Créer la base PostgreSQL et le bucket seulement après décision explicite de lancer la préproduction.
4. Exécuter les migrations Django sur PostgreSQL vide.
5. Transférer les données avec un export/import Django testé d'abord sur une copie ; ne pas copier directement le fichier SQLite vers PostgreSQL.
6. Copier les médias dans le bucket en conservant leurs chemins relatifs.
7. Vérifier comptes, organisations, publications, abonnements Web Push et chaque catégorie de fichier.
8. Tester le retour arrière avant l'ouverture du pilote.

Risques à traiter : différences de séquences d'identifiants après import, périodes d'écriture concurrente, URLs de médias, politique d'accès public/privé du bucket et abonnements Web Push liés à l'origine HTTPS définitive.

## Conditions avant activation

Ne créer l'infrastructure payante qu'après validation explicite des parcours pilotes, de la PWA, du Web Push, des médias et de la migration PostgreSQL. Les estimations de 30–35 € HT/mois en préproduction et d'environ 40 € HT/mois pour le pilote sont des ordres de grandeur à revalider sur les tarifs officiels au moment de la décision.

## Non réalisé volontairement

- aucun compte ou application Scalingo ;
- aucune base PostgreSQL Scalingo ;
- aucun projet, utilisateur, identifiant ou bucket OVHcloud ;
- aucune modification DNS ou HTTPS ;
- aucun déploiement de préproduction ou de production ;
- aucune activation de coût.

## Synthèse Farol

**Décision :** Scalingo Paris retenu comme cible principale pour Éo ; Clever Cloud Paris comme solution de repli ; stockage objet futur S3 en France, avec préférence OVHcloud.

**Statut :** infrastructure future définie et préparée dans les dépôts, mais volontairement non activée pour éviter tout coût avant que le produit soit prêt.

**Réalisé :** compatibilité PostgreSQL par variable d'environnement, serveur Gunicorn, statiques WhiteNoise, stockage média S3 générique et désactivé par défaut, paramètres de sécurité configurables, variables d'exemple, runtime Node fixé, suppression des dépendances de production à des URL locales dans l'inscription et l'API utilisateur, build Next.js vérifié.

**Non réalisé volontairement :** compte Scalingo, base PostgreSQL Scalingo, bucket OVHcloud, DNS, HTTPS, préproduction et production.
