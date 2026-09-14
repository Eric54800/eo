# Éo — démarrage local

Ce dépôt contient l’API Django. L’interface web est un dépôt Git distinct situé dans `eo-web/`.

## Versions vérifiées le 14 septembre 2026

- Python 3.9.6
- Node.js 18.20.8
- npm 10.8.2
- Django 4.2.x
- Next.js 14.2.x

Ces versions décrivent le prototype local actuel. Elles ne constituent pas encore la cible de production. Python 3.9 avec LibreSSL produit notamment un avertissement `urllib3` ; l’environnement de production devra utiliser une version maintenue de Python liée à OpenSSL.

## API Django

Depuis la racine du dépôt :

```sh
python3 -m venv env
source env/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
set -a
source .env
set +a
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Avant le premier lancement, remplacer `DJANGO_SECRET_KEY` dans `.env`. Les valeurs Stripe et Web Push peuvent rester désactivées pour consulter et administrer le prototype sans paiement ni notification.

Contrôles :

```sh
python manage.py check
python manage.py test
```

## Interface Next.js

Dans un second terminal :

```sh
cd eo-web
cp .env.example .env.local
npm ci
npm run dev
```

Ouvrir ensuite `http://127.0.0.1:3000/app`. La variable `NEXT_PUBLIC_API_BASE` doit désigner l’API Django, par défaut `http://127.0.0.1:8000`.

Contrôle avant livraison :

```sh
npm run build
```

## Données locales et sauvegarde

Le prototype utilise actuellement :

- `db.sqlite3` pour la base ;
- `media/` pour les fichiers envoyés.

Ces deux éléments sont exclus de Git et doivent toujours être sauvegardés ensemble. La sauvegarde de référence EO-01 du 14 septembre 2026 se trouve hors du dépôt dans `Documents/50_EO/03_Backups/2026-09-14_EO-01/`.

Une restauration n’est considérée comme validée qu’après contrôle d’intégrité de la base, extraction des médias dans un dossier vide, démarrage de Django sur la copie restaurée et vérification d’une source, d’une criée et d’un document.

## Limites connues

- SQLite et le stockage local des médias conviennent au prototype, pas à la production visée.
- Les paramètres de sécurité de production, PostgreSQL, le stockage objet et les sauvegardes automatiques restent à réaliser dans EO-02.
- Les abonnements Web Push créés sur une adresse TryCloudflare ne seront pas transférés automatiquement au domaine définitif.
