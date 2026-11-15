#!/bin/bash

set -euo pipefail

if [ "$EUID" -ne 0 ]; then
    echo "Erreur : lance ce script avec sudo (sudo bash deploiement_appli.sh)"
    exit 1
fi

IP_APPLI="${IP_APPLI:-192.168.56.10}"
IP_BDD="${IP_BDD:-192.168.56.20}"
MASQUE="${MASQUE:-24}"
INTERFACE_PRIVEE="${INTERFACE_PRIVEE:-enp0s8}"
UTILISATEUR="${SUDO_USER:-root}"
CHEMIN_PROJET="/opt/simulateur-v2x"
DEPOT="https://github.com/zeatyse/Bilon-Kunegel-SAE302.git"
DB_NOM="sae302_traffic"
DB_UTILISATEUR="sae302"
DOSSIER_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================="
echo "  DÉPLOIEMENT DE LA VM APPLICATION"
echo "  IP privée : $IP_APPLI  |  Base de données : $IP_BDD"
echo "========================================="

if ! ip link show "$INTERFACE_PRIVEE" > /dev/null 2>&1; then
    echo "Erreur : l'interface $INTERFACE_PRIVEE n'existe pas. Interfaces disponibles :"
    ip -br link
    echo "Relance avec : sudo INTERFACE_PRIVEE=<nom> bash deploiement_appli.sh"
    exit 1
fi

if grep -Eq "^[^#]*\b$INTERFACE_PRIVEE\b" /etc/network/interfaces; then
    echo "Erreur : $INTERFACE_PRIVEE est déjà configurée dans /etc/network/interfaces."
    echo "Supprime ses lignes de ce fichier puis relance le script."
    exit 1
fi

if [ -z "${DB_MDP:-}" ]; then
    read -r -s -p "Mot de passe de la base (affiché par deploiement_bdd.sh) : " DB_MDP
    echo
fi
if [ -z "$DB_MDP" ]; then
    echo "Erreur : mot de passe vide."
    exit 1
fi

echo -e "\n[1/6] Installation des paquets..."
apt-get update
apt-get install -y python3-mysqldb python3-tk python3-flask git mariadb-client

echo -e "\n[2/6] Configuration de l'interface du réseau privé ($INTERFACE_PRIVEE)..."
cat > /etc/network/interfaces.d/sae302-prive <<EOF
auto $INTERFACE_PRIVEE
iface $INTERFACE_PRIVEE inet static
    address $IP_APPLI/$MASQUE
EOF
if systemctl is-active --quiet NetworkManager; then
    systemctl restart NetworkManager
    sleep 3
fi
ifdown "$INTERFACE_PRIVEE" 2> /dev/null || true
ifup "$INTERFACE_PRIVEE"

echo -e "\n[3/6] Installation du code dans $CHEMIN_PROJET..."
if [ -f "$DOSSIER_SCRIPT/gui/app_gui.py" ] && [ "$DOSSIER_SCRIPT" != "$CHEMIN_PROJET" ]; then
    mkdir -p "$CHEMIN_PROJET"
    cp -a "$DOSSIER_SCRIPT/." "$CHEMIN_PROJET/"
elif [ -d "$CHEMIN_PROJET/.git" ]; then
    git -C "$CHEMIN_PROJET" pull
else
    git clone "$DEPOT" "$CHEMIN_PROJET"
fi

echo -e "\n[4/6] Connexion à la base distante..."
cat > "$CHEMIN_PROJET/config_db.ini" <<EOF
[mariadb]
host = $IP_BDD
user = $DB_UTILISATEUR
password = $DB_MDP
database = $DB_NOM
EOF

echo -e "\n[5/6] Permissions..."
chown -R "$UTILISATEUR":"$UTILISATEUR" "$CHEMIN_PROJET"
chmod -R u=rwX,go=rX "$CHEMIN_PROJET"
chmod 600 "$CHEMIN_PROJET/config_db.ini"

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

echo -e "\n[6/6] Test de connexion à MariaDB ($IP_BDD)..."
if MYSQL_PWD="$DB_MDP" mariadb -h "$IP_BDD" -u "$DB_UTILISATEUR" --connect-timeout=5 \
        -e "SELECT COUNT(*) AS simulations_enregistrees FROM $DB_NOM.simulations;"; then
    RESULTAT_TEST="OK : la VM appli communique avec la base."
else
    RESULTAT_TEST="ÉCHEC : base injoignable. Voir la section Dépannage du README."
fi

echo -e "\n========================================="
echo " VM application prête."
echo " Test BDD : $RESULTAT_TEST"
echo " Raccourcis : 'Simulateur V2X' et 'Tableau de Bord Web V2X'"
echo "========================================="
