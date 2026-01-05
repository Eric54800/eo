# Éo — Code

Ce dossier contient **l’ensemble du code source exécutable** du projet **Éo**.

Le reste du projet (vision, documentation, design, notes, archives) est volontairement
séparé afin de maintenir une distinction claire entre **conception** et **exécution**.

> Rien n’est figé.  
> Le projet Éo évolue **étape par étape**, en restant lisible, compréhensible et maîtrisable.

---

## Objectif

Construire une plateforme **claire, évolutive et durable**,  
au service des **organisations** et des **utilisateurs finaux**.

---

## Philosophie de développement

- **Simplicité** avant sophistication
- **Lisibilité** avant optimisation prématurée
- Chaque décision doit pouvoir être **expliquée simplement**
- La structure doit rester **accueillante pour le futur** (nouveaux modules, nouveaux devs)

---

## Organisation actuelle

02_Code/
└── eo/
├── backend/ # Backend Django
├── core/ # Logique centrale
├── users/ # Gestion des utilisateurs
├── eo-web/ # Frontend (Next.js)
├── env/ # Environnements
├── media/ # Fichiers uploadés
├── manage.py
├── requirements.txt
└── db.sqlite3

---

## Règles importantes

- ⚠️ Les serveurs (backend / frontend) doivent être lancés **uniquement depuis le dossier `eo/`**
- Aucune dépendance conceptuelle avec les dossiers de documentation ou de design
- Toute évolution de structure doit rester **compréhensible sans contexte externe**

---

## Évolution

Cette organisation est **volontairement simple** à ce stade.

Elle pourra évoluer pour :

- mieux séparer frontend / backend
- intégrer de nouveaux services
- préparer la production

Chaque changement devra rester **progressif et justifié**.

---

Projet **Éo**
