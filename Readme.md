nano deploiement_sae302.sh

#!/bin/bash

# Vérification des droits administrateur
if [ "$EUID" -ne 0 ]; then
    echo "❌ Erreur : Veuillez lancer ce script en root (ex: sudo bash deploiement_sae302.sh)"
    exit 1
fi

echo "========================================="
echo "  🚀 DÉPLOIEMENT DU SIMULATEUR V2X 🚀"
echo "========================================="

# 1. Nettoyage et installation des paquets
echo -e "\n[1/4] Nettoyage du cache et installation des dépendances système..."
rm -rf /var/lib/apt/lists/*
apt-get clean
apt-get update
apt-get install -y --fix-missing mariadb-server python3-mysqldb python3-tk git

# 2. Configuration centralisée de la base de données
echo -e "\n[2/4] Configuration de MariaDB et création de la table..."

# Détection intelligente pour éviter de se bloquer si le script est lancé plusieurs fois
if mysql -u root -pmathiskunegel -e "SELECT 1;" &> /dev/null; then
    MYSQL_CMD="mysql -u root -pmathiskunegel"
else
    MYSQL_CMD="mysql -u root"
fi

# On force l'authentification native et on écrase unix_socket
$MYSQL_CMD <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED VIA mysql_native_password;
SET PASSWORD FOR 'root'@'localhost' = PASSWORD('mathiskunegel');
CREATE DATABASE IF NOT EXISTS sae302_traffic;
USE sae302_traffic;
CREATE TABLE IF NOT EXISTS simulations (id_simu INT AUTO_INCREMENT PRIMARY KEY, date_heure DATETIME, taux_trafic INT, direction VARCHAR(50), v2i BOOLEAN, v2v BOOLEAN, temps_ambulance FLOAT);
ALTER TABLE sae302_traffic.simulations ADD UNIQUE (date_heure, taux_trafic, direction, v2i, v2v, temps_ambulance);
FLUSH PRIVILEGES;
EOF

# 3. Récupération du code source
echo -e "\n[3/4] Téléchargement du code depuis GitHub..."
if [ -d "Bilon-Kunegel-SAE302" ]; then
    echo "Le dossier existe déjà, mise à jour du code..."
    cd Bilon-Kunegel-SAE302 && git pull && cd ..
else
    git clone https://github.com/zeatyse/Bilon-Kunegel-SAE302.git
fi

# 4. Création du raccourci d'application
echo -e "\n[4/4] Création du raccourci dans le menu..."
CHEMIN_PROJET=$(pwd)/Bilon-Kunegel-SAE302

cat <<EOF > /usr/share/applications/simulateur-v2x.desktop
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

chmod +x $CHEMIN_PROJET/gui/app_gui.py

echo -e "\n========================================="
echo " ✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS ! ✅"
echo " L'application 'Simulateur V2X' est prête dans votre menu."
echo "========================================="

bash deploiement_sae302.sh
mysql -u root -pmathiskunegel
SELECT * FROM sae302_traffic.simulations;
