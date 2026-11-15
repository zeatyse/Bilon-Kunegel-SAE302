#!/bin/bash

set -euo pipefail

if [ "$EUID" -ne 0 ]; then
    echo "Erreur : lance ce script avec sudo (sudo bash deploiement_bdd.sh)"
    exit 1
fi

IP_BDD="${IP_BDD:-192.168.56.20}"
IP_APPLI="${IP_APPLI:-192.168.56.10}"
MASQUE="${MASQUE:-24}"
RESEAU_PRIVE="${RESEAU_PRIVE:-192.168.56.0/24}"
INTERFACE_PRIVEE="${INTERFACE_PRIVEE:-enp0s8}"
DB_NOM="sae302_traffic"
DB_UTILISATEUR="sae302"
FICHIER_MDP="/root/sae302_mdp_bdd.txt"

echo "========================================="
echo "  DÉPLOIEMENT DE LA VM BASE DE DONNÉES"
echo "  IP privée : $IP_BDD  |  Appli autorisée : $IP_APPLI"
echo "========================================="

if ! ip link show "$INTERFACE_PRIVEE" > /dev/null 2>&1; then
    echo "Erreur : l'interface $INTERFACE_PRIVEE n'existe pas. Interfaces disponibles :"
    ip -br link
    echo "Relance avec : sudo INTERFACE_PRIVEE=<nom> bash deploiement_bdd.sh"
    exit 1
fi

if grep -Eq "^[^#]*\b$INTERFACE_PRIVEE\b" /etc/network/interfaces; then
    echo "Erreur : $INTERFACE_PRIVEE est déjà configurée dans /etc/network/interfaces."
    echo "Supprime ses lignes de ce fichier puis relance le script."
    exit 1
fi

echo -e "\n[1/5] Installation des paquets..."
apt-get update
apt-get install -y mariadb-server nftables openssl

echo -e "\n[2/5] Configuration de l'interface du réseau privé ($INTERFACE_PRIVEE)..."
cat > /etc/network/interfaces.d/sae302-prive <<EOF
auto $INTERFACE_PRIVEE
iface $INTERFACE_PRIVEE inet static
    address $IP_BDD/$MASQUE
EOF
ifdown "$INTERFACE_PRIVEE" 2> /dev/null || true
ifup "$INTERFACE_PRIVEE"

echo -e "\n[3/5] MariaDB en écoute sur le réseau privé uniquement..."
cat > /etc/mysql/mariadb.conf.d/99-sae302.cnf <<EOF
[mysqld]
bind-address = $IP_BDD
EOF
systemctl restart mariadb

echo -e "\n[4/5] Création de la base et de l'utilisateur..."
if [ -f "$FICHIER_MDP" ]; then
    DB_MDP=$(cat "$FICHIER_MDP")
else
    DB_MDP=$(openssl rand -hex 16)
    echo "$DB_MDP" > "$FICHIER_MDP"
    chmod 600 "$FICHIER_MDP"
fi

mariadb <<EOF
CREATE DATABASE IF NOT EXISTS $DB_NOM;
CREATE USER IF NOT EXISTS '$DB_UTILISATEUR'@'$IP_APPLI' IDENTIFIED BY '$DB_MDP';
ALTER USER '$DB_UTILISATEUR'@'$IP_APPLI' IDENTIFIED BY '$DB_MDP';
GRANT SELECT, INSERT ON $DB_NOM.* TO '$DB_UTILISATEUR'@'$IP_APPLI';
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

echo -e "\n[5/5] Pare-feu nftables..."
cat > /etc/nftables.conf <<EOF
flush ruleset

table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;
        iif "lo" accept
        ct state established,related accept
        meta l4proto { icmp, ipv6-icmp } accept
        ip saddr $IP_APPLI tcp dport 3306 accept
        ip saddr $RESEAU_PRIVE tcp dport 22 accept
    }
    chain forward {
        type filter hook forward priority 0; policy drop;
    }
    chain output {
        type filter hook output priority 0; policy accept;
    }
}
EOF
nft -c -f /etc/nftables.conf
systemctl enable nftables
systemctl restart nftables

echo -e "\n========================================="
echo " VM base de données prête."
echo " MariaDB écoute sur $IP_BDD:3306, accessible uniquement depuis $IP_APPLI."
echo ""
echo " Mot de passe de l'utilisateur '$DB_UTILISATEUR' (à donner au script de la VM appli) :"
echo "   $DB_MDP"
echo " Il est aussi enregistré dans $FICHIER_MDP (lisible par root uniquement)."
echo "========================================="
