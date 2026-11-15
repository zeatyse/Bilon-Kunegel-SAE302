import configparser
import csv
import datetime
import os

try:
    import MySQLdb
    MYSQL_DISPONIBLE = True
except ImportError:
    MYSQL_DISPONIBLE = False


RACINE_PROJET = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FICHIER_CONFIG_DB = os.path.join(RACINE_PROJET, "config_db.ini")

CONFIGS_V2X = [
    ("aucun", "Sans V2X"),
    ("v2i", "V2I seul"),
    ("v2v", "V2V seul"),
    ("v2i_v2v", "V2I + V2V"),
]


def cle_config(v2i: bool, v2v: bool) -> str:
    if v2i and v2v:
        return "v2i_v2v"
    if v2i:
        return "v2i"
    if v2v:
        return "v2v"
    return "aucun"


def charger_config_db() -> dict:
    config = {
        "host": "localhost",
        "user": "sae302",
        "passwd": "",
        "db": "sae302_traffic",
    }

    if os.path.exists(FICHIER_CONFIG_DB):
        parser = configparser.ConfigParser()
        parser.read(FICHIER_CONFIG_DB, encoding="utf-8")
        if parser.has_section("mariadb"):
            section = parser["mariadb"]
            config["host"] = section.get("host", config["host"])
            config["user"] = section.get("user", config["user"])
            config["passwd"] = section.get("password", config["passwd"])
            config["db"] = section.get("database", config["db"])

    config["host"] = os.environ.get("SAE302_DB_HOST", config["host"])
    config["user"] = os.environ.get("SAE302_DB_USER", config["user"])
    config["passwd"] = os.environ.get("SAE302_DB_PASSWORD", config["passwd"])
    config["db"] = os.environ.get("SAE302_DB_NAME", config["db"])

    config["charset"] = "utf8mb4"
    config["connect_timeout"] = 2
    return config


class GestionnaireStats:
    def __init__(self, fichier_csv="resultats_simulation.csv"):
        self.fichier_csv = os.path.join(RACINE_PROJET, fichier_csv)
        self._initialiser_csv()
        self.db_config = charger_config_db()

    def _initialiser_csv(self):
        if not os.path.exists(self.fichier_csv):
            with open(self.fichier_csv, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["date_heure", "taux_trafic", "direction", "v2i", "v2v", "temps_ambulance"])

    def enregistrer_resultat(self, taux_trafic: int, direction: str, v2i: bool, v2v: bool, temps_ambulance: float):
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        temps_ambulance = round(temps_ambulance, 2)

        try:
            with open(self.fichier_csv, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([date_str, taux_trafic, direction, v2i, v2v, temps_ambulance])
            print(f"[STATS] Succès : Résultat enregistré dans {self.fichier_csv}")
        except Exception as e:
            print(f"[STATS ERREUR CSV] : {e}")

        if MYSQL_DISPONIBLE and self.db_config["passwd"]:
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
                            row['v2i'] = str(row['v2i']).strip().lower() in ('true', '1', 'yes')
                            row['v2v'] = str(row['v2v']).strip().lower() in ('true', '1', 'yes')
                            row['temps_ambulance'] = round(float(row['temps_ambulance']), 2)
                            resultats.append(row)
                        except Exception:
                            continue
            except Exception as e:
                print(f"[CSV ERREUR LECTURE] : {e}")
        return resultats

    @staticmethod
    def moyennes_par_scenario(resultats):
        groupes = {}
        for r in resultats:
            cle = (r['taux_trafic'], r['direction'])
            groupe = groupes.setdefault(cle, {c: [] for c, _ in CONFIGS_V2X})
            groupe[cle_config(r['v2i'], r['v2v'])].append(r['temps_ambulance'])

        scenarios = []
        for (taux, direction), temps in sorted(groupes.items()):
            moyennes = {}
            for config, _ in CONFIGS_V2X:
                valeurs = temps[config]
                moyennes[config] = {
                    "moyenne": round(sum(valeurs) / len(valeurs), 2) if valeurs else None,
                    "nb": len(valeurs),
                }

            sans = moyennes["aucun"]["moyenne"]
            avec = moyennes["v2i_v2v"]["moyenne"]
            gain = round(sans - avec, 2) if sans is not None and avec is not None else None

            scenarios.append({
                "taux_trafic": taux,
                "direction": direction,
                "moyennes": moyennes,
                "gain": gain,
            })
        return scenarios
