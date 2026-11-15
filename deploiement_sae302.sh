#!/bin/bash

set -euo pipefail

if [ "$EUID" -ne 0 ]; then
    echo "Erreur : lance ce script avec sudo (sudo bash deploiement_sae302.sh)"
    exit 1
fi

UTILISATEUR="${SUDO_USER:-root}"
CHEMIN_PROJET="/opt/simulateur-v2x"
DB_NOM="sae302_traffic"
DB_UTILISATEUR="sae302"

echo "========================================="
echo "  DÉPLOIEMENT DU SIMULATEUR V2X"
echo "========================================="

echo -e "\n[1/5] Installation des dépendances..."
apt-get update
apt-get install -y mariadb-server python3-mysqldb python3-tk python3-flask git openssl

echo -e "\n[2/5] Récupération du code..."
if [ -d "$CHEMIN_PROJET/.git" ]; then
    git -C "$CHEMIN_PROJET" pull
else
    git clone https://github.com/zeatyse/Bilon-Kunegel-SAE302.git "$CHEMIN_PROJET"
fi

echo -e "\n[3/5] Configuration de MariaDB..."
FICHIER_CONFIG="$CHEMIN_PROJET/config_db.ini"

if [ -f "$FICHIER_CONFIG" ]; then
    DB_MDP=$(sed -n 's/^password *= *//p' "$FICHIER_CONFIG")
else
    DB_MDP=$(openssl rand -hex 16)
fi

mysql <<EOF
CREATE DATABASE IF NOT EXISTS $DB_NOM;
CREATE USER IF NOT EXISTS '$DB_UTILISATEUR'@'localhost' IDENTIFIED BY '$DB_MDP';
ALTER USER '$DB_UTILISATEUR'@'localhost' IDENTIFIED BY '$DB_MDP';
GRANT SELECT, INSERT ON $DB_NOM.* TO '$DB_UTILISATEUR'@'localhost';
USE $DB_NOM;
CREATE TABLE IF NOT EXISTS simulations (
    id_simu INT AUTO_INCREMENT PRIMARY KEY,
    date_heure DATETIME,
    taux_trafic INT,
    direction VARCHAR(50),
    v2i BOOLEAN,
    v2v BOOLEAN,
    temps_ambulance FLOAT
);
FLUSH PRIVILEGES;
EOF

cat > "$FICHIER_CONFIG" <<EOF
[mariadb]
host = localhost
user = $DB_UTILISATEUR
password = $DB_MDP
database = $DB_NOM
EOF

echo -e "\n[4/5] Application des permissions..."
chown -R "$UTILISATEUR":"$UTILISATEUR" "$CHEMIN_PROJET"
chmod -R u=rwX,go=rX "$CHEMIN_PROJET"
chmod 600 "$FICHIER_CONFIG"

echo -e "\n[5/5] Création des raccourcis..."
cat > /usr/share/applications/simulateur-v2x.desktop <<EOF
[Desktop Entry]
Version=1.0
Name=Simulateur V2X
Comment=Simulation de trafic routier SAE302
Exec=python3 $CHEMIN_PROJET/gui/app_gui.py
Path=$CHEMIN_PROJET/
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Education;Science;
EOF

cat > /usr/share/applications/serveur-web-v2x.desktop <<EOF
[Desktop Entry]
Version=1.0
Name=Tableau de Bord Web V2X
Comment=Serveur web Flask (http://127.0.0.1:5000)
Exec=python3 $CHEMIN_PROJET/web/flask_web.py
Path=$CHEMIN_PROJET/
Icon=web-browser
Terminal=true
Type=Application
Categories=Education;Science;
EOF

echo -e "\n========================================="
echo " Déploiement terminé."
echo " Raccourcis : 'Simulateur V2X' et 'Tableau de Bord Web V2X'"
echo " Identifiants BDD : $FICHIER_CONFIG (accessible à $UTILISATEUR uniquement)"
echo "========================================="
