import os
import sys
from flask import Flask, render_template, send_file

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from modele.gestionnaire_stats import GestionnaireStats

app = Flask(__name__)
stats_manager = GestionnaireStats()

@app.route('/')
def index():
    print("[DEBUG] Requête reçue sur la page d'accueil")
    try:
        resultats = stats_manager.recuperer_resultats()
        print(f"[DEBUG] {len(resultats)} lignes chargées depuis le CSV.")

        temps_avec_v2x = [float(r['temps_ambulance']) for r in resultats if r.get('v2i') or r.get('v2v')]
        temps_sans_v2x = [float(r['temps_ambulance']) for r in resultats if not r.get('v2i') and not r.get('v2v')]

        moy_avec = sum(temps_avec_v2x) / len(temps_avec_v2x) if temps_avec_v2x else 0
        moy_sans = sum(temps_sans_v2x) / len(temps_sans_v2x) if temps_sans_v2x else 0
        diff = moy_sans - moy_avec if (moy_avec and moy_sans) else 0

        return render_template('index.html', resultats=resultats, moy_avec=round(moy_avec, 2), moy_sans=round(moy_sans, 2), diff=round(diff, 2))
    except Exception as e:
        print(f"[ERREUR DANS INDEX] : {e}")
        return f"Erreur interne du serveur : {e}", 500

@app.route('/export')
def export_csv():
    if os.path.exists(stats_manager.fichier_csv):
        return send_file(stats_manager.fichier_csv, as_attachment=True, download_name="export_statistiques_v2x.csv")
    return "Aucun fichier CSV disponible.", 404

if __name__ == '__main__':
    # debug=False évite les blocages du reloader automatique de Flask sous Windows
    app.run(debug=False, port=5000)