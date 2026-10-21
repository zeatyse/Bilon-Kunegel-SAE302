import csv
import datetime
import os

# Tentative d'importation de mysqlclient (optionnel pour éviter les crashs si non installé)
try:
    import MySQLdb
    MYSQL_DISPONIBLE = True
except ImportError:
    MYSQL_DISPONIBLE = False


class GestionnaireStats:
    def __init__(self, fichier_csv="resultats_simulation.csv"):
        # Force la création du CSV dans la racine du projet
        racine_projet = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.fichier_csv = os.path.join(racine_projet, fichier_csv)
        self._initialiser_csv()

        # Identifiants de connexion MariaDB
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'passwd': 'mathiskunegel',
            'db': 'sae302_traffic',
            'charset': 'utf8mb4'
        }

    def _initialiser_csv(self):
        if not os.path.exists(self.fichier_csv):
            with open(self.fichier_csv, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["date_heure", "taux_trafic", "direction", "v2i", "v2v", "temps_ambulance"])

    def enregistrer_resultat(self, taux_trafic: int, direction: str, v2i: bool, v2v: bool, temps_ambulance: float):
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Sauvegarde CSV locale (Garanti à chaque fin de simulation)
        try:
            with open(self.fichier_csv, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([date_str, taux_trafic, direction, v2i, v2v, temps_ambulance])
            print(f"[STATS] Succès : Résultat enregistré dans {self.fichier_csv}")
        except Exception as e:
            print(f"[STATS ERREUR CSV] : {e}")

        # 2. Envoi vers MariaDB (uniquement si le module est installé et configuré)
        if MYSQL_DISPONIBLE:
            self.inserer_dans_mariadb(date_str, taux_trafic, direction, v2i, v2v, temps_ambulance)
        else:
            print("[MARIADB] Module 'mysqlclient' non installé sur cette machine (sauvegarde CSV uniquement).")

    def inserer_dans_mariadb(self, date_str, taux_trafic, direction, v2i, v2v, temps_ambulance):
        try:
            conn = MySQLdb.connect(**self.db_config)
            cursor = conn.cursor()

            query = """
                INSERT INTO simulations 
                (date_heure, taux_trafic, direction, v2i, v2v, temps_ambulance) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            valeurs = (date_str, taux_trafic, direction, v2i, v2v, temps_ambulance)

            cursor.execute(query, valeurs)
            conn.commit()

            cursor.close()
            conn.close()
            print("[MARIADB] Enregistrement réussi dans la base de données !")

        except Exception as err:
            print(f"[MARIADB ERREUR] Connexion impossible : {err}")
