# Méthodologie Gérard

Prototype local en français. Python 3.9+ ; aucune installation de bibliothèque nécessaire.

## Démarrage

Dans le répertoire du projet :

```sh
python3 server.py
```

Ouvrir http://127.0.0.1:8765. Garder le terminal ouvert ; Ctrl+C arrête le serveur. En cas de port occupé : `python3 server.py --port 8766`.

Sur macOS, le fichier `Demarrer.command` permet également de démarrer par double-clic.

## Utilisation

1. Charger l’exemple fictif ou créer une course.
2. Ajouter les chevaux, leurs données brutes et leurs évaluations de 0 à 10.
3. Calculer le classement et ouvrir le détail des points.
4. Enregistrer explicitement la course. L’historique permet de la rouvrir et de modifier ses partants, son barème ou les places à l’arrivée.
5. Exporter une analyse en JSON si souhaité.

## Barème provisoire

Les échanges d’origine ne fixaient pas une formule définitive. Le MVP propose des poids modifiables : classe 20, forme 15, vitesse 15, confrontations 10, valeur 8, poids 7, corde 5, terrain 5, distance 5, parcours 3, tactique 3, âge/sexe 2, entourage 2.

Note = somme(évaluation / 10 × coefficient) / somme(coefficients) × 100.
Les critères inconnus contribuent zéro sans renormalisation : une note incomplète est une borne minimale. La couverture correspond au pourcentage de coefficients renseignés et ne constitue pas un indice de confiance prédictive. Les ex æquo sont ordonnés par numéro. Les notes de détail sont arrondies indépendamment.

Les caractéristiques brutes ne sont pas automatiquement converties en aptitudes : les évaluations restent manuelles et contextualisées. Aucune décharge réglementaire n’est appliquée automatiquement. Les observations accueillent les confrontations, sources et justifications. Aucun flux de courses réelles, pari, apprentissage statistique ou compte utilisateur n’est inclus.

## Structure et conservation

- `frontend/` : interface HTML, CSS et JavaScript.
- `server.py` : serveur HTTP limité à 127.0.0.1, validation, calcul et API SQLite.
- `data/gerard.sqlite3` : base créée au premier lancement, une analyse complète par course (chevaux, critères, coefficients, arrivée).
- `tests/` : vérifications du calcul, des entrées et de la persistance.

Sauvegarder le fichier SQLite lorsque le serveur est arrêté. L’historique conserve l’état courant de chaque course ; enregistrer une course existante la met à jour, sans créer de version intermédiaire. Les saisies non enregistrées ne sont pas conservées après fermeture. Le JSON est un export portable ; son import n’est pas encore proposé.

Tests : `python3 -m unittest discover -s tests -v`.
