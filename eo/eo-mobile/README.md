# EO Mobile

Squelette Expo pour l'application publique anonyme.

## Objectif

Cette base couvre `EO-A07`:
- application mobile sans authentification
- client API publique
- persistance locale des structures suivies
- navigation simple entre liste et detail structure

## Demarrage

```bash
cd /Users/ericbarthelemy/Documents/50_EO/02_Code/eo/eo-mobile
npm install
npm run start
```

## Configuration

L'URL de l'API publique est definie dans `app.json`:

```json
{
  "expo": {
    "extra": {
      "publicApiBaseUrl": "http://127.0.0.1:8000/api/public"
    }
  }
}
```

Pour un appareil physique, remplace `127.0.0.1` par l'IP locale de la machine qui heberge Django.

## Etat actuel

Disponible:
- liste publique des structures
- detail public d'une structure
- liste des criées publiees d'une structure
- suivi local des structures via `AsyncStorage`
- preferences locales de notifications par structure
- fil agrege des criées des structures suivies

Non implemente:
- envoi push natif par topic de structure
- deep links
- design final
