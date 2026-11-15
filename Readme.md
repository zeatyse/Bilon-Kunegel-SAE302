# Simulateur V2X — SAE302

Simulation d'un carrefour à feux tricolores avec passage prioritaire d'une ambulance. Le projet compare le temps de traversée de l'ambulance selon le niveau de trafic, sa direction et les communications V2X activées : V2I (l'ambulance demande le vert au carrefour) et V2V (l'ambulance prévient les véhicules devant elle, qui réagissent plus vite).

L'application et la base de données tournent sur deux machines virtuelles Debian séparées. La VM base de données n'est joignable que depuis la VM application, par un réseau privé.

---

## 1. Architecture

```
                     Réseau local (salle de TP)
                                  │
                         Accès par pont (enp0s3)
                          adresse en DHCP
                                  │
                   ┌──────────────┴──────────────┐
                   │          VM APPLI           │
                   │  Debian + bureau            │
                   │  Simulateur Tkinter         │
                   │  Tableau de bord Flask      │
                   │  192.168.56.10              │
                   └──────────────┬──────────────┘
                                  │
                   Réseau privé hôte (enp0s8)  192.168.56.0/24
                                  │
                   ┌──────────────┴──────────────┐
                   │           VM BDD            │
                   │  Debian sans bureau         │
                   │  MariaDB (port 3306)        │
                   │  Pare-feu nftables          │
                   │  192.168.56.20              │
                   └──────────────┬──────────────┘
                                  │
                            NAT (enp0s3)
                     sortie Internet uniquement
```

| VM | Carte 1 | Carte 2 | Rôle |
|---|---|---|---|
| VM appli | Accès par pont (`enp0s3`, DHCP) | Réseau privé hôte (`enp0s8`, `192.168.56.10/24`) | Interface graphique, serveur web, accès Internet |
| VM BDD | NAT (`enp0s3`, automatique) | Réseau privé hôte (`enp0s8`, `192.168.56.20/24`) | Base MariaDB |

La carte NAT donne à la VM BDD un accès Internet sortant, pour installer les paquets et faire les mises à jour. Le NAT ne laisse rien entrer : depuis le réseau local, la VM BDD reste invisible. La seule porte d'entrée vers la base est le réseau privé, depuis la VM appli.

Les flux autorisés vers la VM BDD sont :

| Source | Port | Usage |
|---|---|---|
| `192.168.56.10` (VM appli uniquement) | TCP 3306 | MariaDB |
| `192.168.56.0/24` | TCP 22 | SSH d'administration (si installé) |
| tout le réseau privé | ICMP | ping de diagnostic |

Tout le reste est bloqué par le pare-feu.

---

## 2. Contenu du dépôt

```
modele/                 Classes métier : Vehicule, Ambulance, FeuTricolore, FileAttente, Carrefour, GestionnaireStats
gui/                    Interface graphique Tkinter (simulation animée)
web/                    Tableau de bord Flask (comparaison des résultats, export CSV)
main.py                 Version console de la simulation
deploiement_bdd.sh      Script d'installation de la VM base de données
deploiement_appli.sh    Script d'installation de la VM application
requirements.txt        Dépendances Python (installation manuelle hors Debian)
```

---

## 3. Préparer VirtualBox

### 3.1 Le réseau privé hôte

1. Dans VirtualBox, ouvrir **Fichier > Outils > Gestionnaire de réseau**, onglet **Réseaux privés hôte**.
2. S'il n'y en a pas, cliquer sur **Créer**. Le réseau créé s'appelle en général `vboxnet0` (Linux/macOS) ou `VirtualBox Host-Only Ethernet Adapter` (Windows).
3. Vérifier que son adresse est `192.168.56.1` avec le masque `255.255.255.0`.

Les IP `192.168.56.10` et `192.168.56.20` sont fixes et en dehors de la plage DHCP de VirtualBox (qui commence à `.100`), donc il n'y a pas de conflit.

Si le réseau privé hôte utilise un autre sous-réseau, il suffit de donner les bonnes adresses aux scripts (voir la partie 6).

> Un **Réseau interne** VirtualBox fonctionne aussi : il suffit de choisir le même nom de réseau interne (par exemple `intnet`) sur les deux VM. La différence est que la machine hôte ne peut alors pas joindre les VM par ce réseau.

### 3.2 Image Debian

Les deux VM utilisent la même ISO Debian (Debian 12 ou 13, `netinst` amd64).

---

## 4. Installer la VM base de données (à faire en premier)

### 4.1 Créer la VM

1. **Nouvelle machine** : nom `vm-bdd`, type Linux, version Debian 64-bit, 1 Go de RAM et 10 Go de disque suffisent.
2. **Configuration > Réseau** :
   - **Carte 1** : activée, mode d'accès **NAT**.
   - **Carte 2** : activée, mode d'accès **Réseau privé hôte**, nom `vboxnet0` (ou l'adaptateur Host-Only sous Windows).

### 4.2 Installer Debian

1. Lancer l'installation normale.
2. À l'étape réseau, si Debian demande l'interface principale, choisir **`enp0s3`** (la carte NAT).
3. À l'étape **Sélection des logiciels** :
   - décocher **Environnement de bureau Debian** et tous les bureaux (GNOME, Xfce…) ;
   - cocher **Utilitaires usuels du système** ;
   - cocher **Serveur SSH** si tu veux administrer la VM depuis la VM appli (optionnel).
4. Terminer l'installation et redémarrer.

### 4.3 Récupérer le script

La VM a Internet grâce à la carte NAT. Le plus simple est de cloner le dépôt :

```bash
su -
apt install -y git
git clone https://github.com/zeatyse/Bilon-Kunegel-SAE302.git
cd Bilon-Kunegel-SAE302
```

Il faut que la dernière version du projet (avec `deploiement_bdd.sh`) soit poussée sur GitHub avant. Sinon, le script peut être copié par n'importe quel autre moyen : dossier partagé VirtualBox, clé USB, etc.

> Si un mot de passe root a été défini pendant l'installation, l'utilisateur normal n'a pas `sudo` : il faut passer par `su -`, puis lancer les commandes sans `sudo`. Dans ce cas, tape `bash deploiement_bdd.sh` au lieu de `sudo bash deploiement_bdd.sh`.

### 4.4 Lancer le script

```bash
sudo bash deploiement_bdd.sh
```

Le script effectue cinq étapes :

1. **Paquets** : installe `mariadb-server`, `nftables` et `openssl`.
2. **Réseau privé** : crée `/etc/network/interfaces.d/sae302-prive`, qui donne l'IP fixe `192.168.56.20/24` à `enp0s8`, puis active l'interface.
3. **MariaDB** : crée `/etc/mysql/mariadb.conf.d/99-sae302.cnf` avec `bind-address = 192.168.56.20`. MariaDB n'écoute donc que sur le réseau privé, jamais sur une autre interface.
4. **Base et utilisateur** : crée la base `sae302_traffic`, la table `simulations` et l'utilisateur `sae302` :
   - il ne peut se connecter **que depuis `192.168.56.10`** (`'sae302'@'192.168.56.10'`) ;
   - il n'a que les droits **SELECT** et **INSERT** sur `sae302_traffic` ;
   - son mot de passe est généré aléatoirement (32 caractères) et enregistré dans `/root/sae302_mdp_bdd.txt` (droits 600).
5. **Pare-feu** : écrit `/etc/nftables.conf` (politique par défaut : tout bloquer en entrée, sauf les flux du tableau de la partie 1) et active nftables au démarrage.

À la fin, le script **affiche le mot de passe de l'utilisateur `sae302`**. Il faut le noter, car il sera demandé sur la VM appli. Il reste consultable plus tard avec :

```bash
sudo cat /root/sae302_mdp_bdd.txt
```

Le script peut être relancé sans risque : il réutilise le même mot de passe.

### 4.5 Vérifier la VM BDD

```bash
ip -br address
```

`enp0s8` doit avoir l'adresse `192.168.56.20/24`, et `enp0s3` une adresse en `10.0.2.x` (NAT).

```bash
sudo ss -tlnp | grep 3306
```

On doit voir `192.168.56.20:3306`, et non `0.0.0.0:3306` ni `127.0.0.1:3306`.

```bash
sudo nft list ruleset
```

On doit retrouver les règles du pare-feu avec `policy drop`.

---

## 5. Installer la VM application

### 5.1 Créer la VM

1. **Nouvelle machine** : nom `vm-appli`, Debian 64-bit, 2 Go de RAM et 20 Go de disque.
2. **Configuration > Réseau** :
   - **Carte 1** : activée, mode d'accès **Accès par pont**, nom : la carte physique du PC (Wi-Fi ou Ethernet).
   - **Carte 2** : activée, mode d'accès **Réseau privé hôte**, même réseau que la VM BDD (`vboxnet0`).

### 5.2 Installer Debian

1. Installation normale. À l'étape réseau, choisir **`enp0s3`** (la carte en pont) comme interface principale.
2. À l'étape **Sélection des logiciels**, garder un **environnement de bureau** (GNOME ou Xfce) : l'application a une interface graphique.

### 5.3 Récupérer le projet

```bash
sudo apt install -y git
git clone https://github.com/zeatyse/Bilon-Kunegel-SAE302.git
cd Bilon-Kunegel-SAE302
```

Il est aussi possible de copier et décompresser le zip du projet, puis de se placer dans son dossier.

### 5.4 Lancer le script

```bash
sudo bash deploiement_appli.sh
```

Le script demande le mot de passe affiché par `deploiement_bdd.sh` (la saisie est masquée). Il effectue ensuite six étapes :

1. **Paquets** : installe `python3-tk`, `python3-flask`, `python3-mysqldb`, `git` et `mariadb-client` (ce dernier sert au test de connexion).
2. **Réseau privé** : donne l'IP fixe `192.168.56.10/24` à `enp0s8`. Si NetworkManager est actif (cas d'une VM avec bureau), il est redémarré pour laisser cette interface à la configuration du script.
3. **Code** : copie le projet dans `/opt/simulateur-v2x`. Si le script est lancé depuis le dossier du projet, c'est cette copie locale qui est installée. Sinon, il clone le dépôt GitHub.
4. **Connexion à la base** : crée `/opt/simulateur-v2x/config_db.ini` avec l'adresse de la VM BDD (`192.168.56.20`), l'utilisateur `sae302` et le mot de passe.
5. **Permissions** : le dossier appartient à l'utilisateur qui a lancé `sudo`, avec des droits normaux (aucun `chmod 777`). `config_db.ini` est en 600, donc lisible par cet utilisateur uniquement. Le script crée aussi les raccourcis **Simulateur V2X** et **Tableau de Bord Web V2X** dans le menu.
6. **Test** : se connecte à MariaDB sur la VM BDD et affiche le nombre de simulations enregistrées. Le résultat du test est rappelé à la fin.

### 5.5 Vérifier la liaison entre les deux VM

Depuis la VM appli :

```bash
ping -c 2 192.168.56.20
```

```bash
mariadb -h 192.168.56.20 -u sae302 -p -e "SELECT * FROM sae302_traffic.simulations;"
```

Les deux commandes doivent fonctionner.

Depuis le PC hôte ou une autre machine du réseau local, la base ne doit pas répondre, car la VM BDD n'accepte le port 3306 que depuis `192.168.56.10` :

```bash
nc -zv -w 3 192.168.56.20 3306
```

---

## 6. Changer les adresses

Les adresses par défaut sont modifiables en les passant aux scripts. Il faut utiliser les **mêmes valeurs sur les deux VM**.

| Variable | Défaut | Script(s) |
|---|---|---|
| `IP_APPLI` | `192.168.56.10` | les deux |
| `IP_BDD` | `192.168.56.20` | les deux |
| `MASQUE` | `24` | les deux |
| `RESEAU_PRIVE` | `192.168.56.0/24` | `deploiement_bdd.sh` (autorisation SSH) |
| `INTERFACE_PRIVEE` | `enp0s8` | les deux |
| `DB_MDP` | demandé au clavier | `deploiement_appli.sh` |

Exemple avec un réseau `192.168.100.0/24` :

```bash
sudo IP_APPLI=192.168.100.10 IP_BDD=192.168.100.20 RESEAU_PRIVE=192.168.100.0/24 bash deploiement_bdd.sh
```

```bash
sudo IP_APPLI=192.168.100.10 IP_BDD=192.168.100.20 bash deploiement_appli.sh
```

---

## 7. Utilisation

Sur la VM appli, depuis le menu des applications :

- **Simulateur V2X** ouvre la simulation. Chaque essai terminé est enregistré dans `resultats_simulation.csv` (dans `/opt/simulateur-v2x`) et dans la table `simulations` de la VM BDD.
- **Tableau de Bord Web V2X** lance le serveur Flask. Le tableau de bord est accessible dans le navigateur de la VM appli à l'adresse `http://127.0.0.1:5000`.

Les commandes équivalentes en terminal sont :

```bash
cd /opt/simulateur-v2x
python3 gui/app_gui.py
```

```bash
cd /opt/simulateur-v2x
python3 web/flask_web.py
```

Le serveur web n'écoute qu'en local. Pour l'ouvrir au réseau en pont, il faut remplacer `127.0.0.1` par `0.0.0.0` dans la dernière ligne de `web/flask_web.py`.

---

## 8. Configuration de la connexion à la base

Les identifiants ne sont jamais écrits dans le code. L'application les lit dans cet ordre de priorité :

1. les variables d'environnement `SAE302_DB_HOST`, `SAE302_DB_USER`, `SAE302_DB_PASSWORD` et `SAE302_DB_NAME` ;
2. le fichier `config_db.ini` à la racine du projet (créé par `deploiement_appli.sh` et exclu de Git) :

```ini
[mariadb]
host = 192.168.56.20
user = sae302
password = ...
database = sae302_traffic
```

Sans mot de passe configuré, l'application enregistre uniquement dans le CSV.

---

## 9. Mesure et analyse

Le chronomètre démarre à l'arrivée de l'ambulance et s'arrête quand elle a quitté le carrefour.

Le tableau de bord ne compare que des simulations faites dans les mêmes conditions (même trafic, même direction), parce qu'une moyenne globale mélangerait des scénarios différents. Un scénario n'est comparable que s'il a été testé avec et sans V2X.

La requête équivalente, à lancer sur la VM BDD (`sudo mariadb`), est :

```sql
SELECT direction, taux_trafic, v2i, v2v,
       COUNT(*) AS nombre_de_tests,
       ROUND(AVG(temps_ambulance), 2) AS temps_moyen
FROM sae302_traffic.simulations
GROUP BY direction, taux_trafic, v2i, v2v
ORDER BY direction, taux_trafic, v2i, v2v;
```

---

## 10. Choix de sécurité

| Mesure | Effet |
|---|---|
| Base sur une VM séparée, sans carte en pont | La base n'est pas exposée au réseau local |
| Carte NAT sur la VM BDD | Sortie Internet pour les mises à jour, aucune connexion entrante possible |
| `bind-address` sur l'IP privée | MariaDB n'écoute que sur le réseau privé |
| Utilisateur `sae302@192.168.56.10` | Le compte n'est utilisable que depuis la VM appli |
| Droits SELECT et INSERT uniquement | Impossible de supprimer ou modifier les données depuis l'appli |
| Pare-feu nftables en `policy drop` | Seul le port 3306 est ouvert, et seulement pour la VM appli |
| Compte root MariaDB non modifié | root reste accessible uniquement en local sur la VM BDD, par socket Unix |
| Mot de passe aléatoire, hors du code | Rien de sensible dans le dépôt Git |
| `config_db.ini` en 600 et dans `.gitignore` | Le mot de passe n'est lisible que par l'utilisateur de l'appli |

---

## 11. Dépannage

**« l'interface enp0s8 n'existe pas »**
Les noms d'interface peuvent varier. Afficher la liste avec `ip -br link`, puis relancer le script avec le bon nom :

```bash
sudo INTERFACE_PRIVEE=enp0s9 bash deploiement_bdd.sh
```

**« enp0s8 est déjà configurée dans /etc/network/interfaces »**
L'installateur Debian a déjà configuré cette carte. Supprimer les lignes qui la concernent dans `/etc/network/interfaces` (`sudo nano /etc/network/interfaces`), puis relancer le script.

**Le test de connexion échoue à la fin de `deploiement_appli.sh`**
Vérifier dans l'ordre :

1. `ping 192.168.56.20` depuis la VM appli. Si le ping échoue, les deux cartes 2 ne sont pas sur le même réseau privé hôte dans VirtualBox, ou l'une des IP n'est pas appliquée (vérifier avec `ip -br address` sur chaque VM).
2. Sur la VM BDD, `sudo systemctl status mariadb` et `sudo ss -tlnp | grep 3306`.
3. Sur la VM BDD, `sudo nft list ruleset` : l'IP autorisée doit être celle de la VM appli.
4. Le mot de passe : `sudo cat /root/sae302_mdp_bdd.txt` sur la VM BDD, puis relancer `deploiement_appli.sh` sur la VM appli.
5. Si l'IP de la VM appli a changé, relancer `deploiement_bdd.sh` avec la bonne valeur de `IP_APPLI`.

**MariaDB ne démarre plus au boot de la VM BDD (« Can't assign requested address »)**
L'IP privée n'était pas encore active au démarrage de MariaDB. Lancer `sudo ifup enp0s8`, puis `sudo systemctl restart mariadb`, et vérifier que `/etc/network/interfaces.d/sae302-prive` existe bien.

**Les résultats n'arrivent que dans le CSV**
Vérifier que `/opt/simulateur-v2x/config_db.ini` existe et contient un mot de passe, et que `python3-mysqldb` est installé. Les erreurs de connexion s'affichent dans le terminal avec le préfixe `[MARIADB ERREUR]`.

---

## Auteurs

Bilon — Kunegel, BUT Réseaux et Télécommunications.
