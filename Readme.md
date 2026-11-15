# Simulateur V2X — SAE302

Simulation d'un carrefour à feux tricolores avec passage prioritaire d'une ambulance. Le projet compare le temps de traversée de l'ambulance selon le niveau de trafic, sa direction et les communications V2X activées : V2I (l'ambulance demande le vert au carrefour) et V2V (l'ambulance prévient les véhicules devant elle, qui réagissent plus vite).

## Structure

```
modele/       Classes métier : Vehicule, Ambulance, FeuTricolore, FileAttente, Carrefour, GestionnaireStats
gui/          Interface graphique Tkinter (simulation animée)
web/          Tableau de bord Flask (comparaison des résultats, export CSV)
main.py       Version console de la simulation
```

Chaque simulation lancée depuis l'interface enregistre le temps de l'ambulance dans `resultats_simulation.csv` et, si MariaDB est configurée, dans la table `simulations`.

## Installation rapide (Debian/Ubuntu)

```bash
sudo bash deploiement_sae302.sh
```

Le script installe les dépendances, clone le projet dans `/opt/simulateur-v2x`, crée la base `sae302_traffic` avec un utilisateur dédié `sae302` (droits SELECT/INSERT uniquement), puis ajoute deux raccourcis au menu.

## Lancement manuel

```bash
pip install -r requirements.txt
python3 gui/app_gui.py
python3 web/flask_web.py
```

MariaDB est optionnelle : sans configuration, les résultats sont seulement écrits dans le CSV.

## Configuration de la base de données

Les identifiants ne sont jamais dans le code. Ils sont lus dans cet ordre :

1. Variables d'environnement : `SAE302_DB_HOST`, `SAE302_DB_USER`, `SAE302_DB_PASSWORD`, `SAE302_DB_NAME`
2. Fichier `config_db.ini` à la racine du projet (créé par le script, exclu de Git) :

```ini
[mariadb]
host = localhost
user = sae302
password = ...
database = sae302_traffic
```

## Mesure et analyse

Le chronomètre démarre à l'arrivée de l'ambulance et s'arrête quand elle a quitté le carrefour. Le tableau de bord ne compare que des simulations faites dans les mêmes conditions (même trafic, même direction), car une moyenne globale mélangerait des scénarios différents.

Requête équivalente côté MariaDB :

```sql
SELECT direction, taux_trafic, v2i, v2v,
       COUNT(*) AS nombre_de_tests,
       ROUND(AVG(temps_ambulance), 2) AS temps_moyen
FROM sae302_traffic.simulations
GROUP BY direction, taux_trafic, v2i, v2v
ORDER BY direction, taux_trafic, v2i, v2v;
```

## Auteurs

Bilon — Kunegel, BUT Réseaux et Télécommunications.
