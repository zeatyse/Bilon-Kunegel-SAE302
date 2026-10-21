import csv
import datetime
import os

try:
    import MySQLdb
    MYSQL_DISPONIBLE = True
except ImportError:
    MYSQL_DISPONIBLE = False


class GestionnaireStats:
    def __init__(self, fichier_csv="resultats_simulation.csv"):
        racine_projet = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.fichier_csv = os.path.join(racine_projet, fichier_csv)
        self._initialiser_csv()

        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'passwd': 'mathiskunegel',
            'db': 'sae302_traffic',
            'charset': 'utf8mb4',
            'connect_timeout': 2
        }

    def _initialiser_csv(self):
        if not os.path.exists(self.fichier_csv):
            with open(self.fichier_csv, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["date_heure", "taux_trafic", "direction", "v2i", "v2v", "temps_ambulance"])

    def enregistrer_resultat(self, taux_trafic: int, direction: str, v2i: bool, v2v: bool, temps_ambulance: float):
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with open(self.fichier_csv, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([date_str, taux_trafic, direction, v2i, v2v, temps_ambulance])
            print(f"[STATS] Succès : Résultat enregistré dans {self.fichier_csv}")
        except Exception as e:
            print(f"[STATS ERREUR CSV] : {e}")

        if MYSQL_DISPONIBLE:
            self.inserer_dans_mariadb(date_str, taux_trafic, direction, v2i, v2v, temps_ambulance)

    def inserer_dans_mariadb(self, date_str, taux_trafic, direction, v2i, v2v, temps_ambulance):
        try:
            conn = MySQLdb.connect(**self.db_config)
            cursor = conn.cursor()
            query = """
                INSERT INTO simulations 
                (date_heure, taux_trafic, direction, v2i, v2v, temps_ambulance) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (date_str, taux_trafic, direction, v2i, v2v, temps_ambulance))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as err:
            print(f"[MARIADB ERREUR] Connexion impossible : {err}")

    def recuperer_resultats(self):
        resultats = []
        if os.path.exists(self.fichier_csv) and os.path.getsize(self.fichier_csv) > 0:
            try:
                with open(self.fichier_csv, mode='r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            row['taux_trafic'] = int(row['taux_trafic'])
                            # Conversion sécurisée des booléens CSV (string vers bool)
                            row['v2i'] = str(row['v2i']).strip().lower() in ('true', '1', 'yes')
                            row['v2v'] = str(row['v2v']).strip().lower() in ('true', '1', 'yes')
                            row['temps_ambulance'] = round(float(row['temps_ambulance']), 2)
                            resultats.append(row)
                        except Exception:
                            continue # Ignore les lignes corrompues si y en a
            except Exception as e:
                print(f"[CSV ERREUR LECTURE] : {e}")
        return resultats