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

def charger_et_analyser_stats():
    resultats = stats_manager.recuperer_resultats()

    temps_avec_v2x = [r['temps_ambulance'] for r in resultats if r['v2i'] or r['v2v']]
    temps_sans_v2x = [r['temps_ambulance'] for r in resultats if not r['v2i'] and not r['v2v']]

    moy_avec = sum(temps_avec_v2x) / len(temps_avec_v2x) if temps_avec_v2x else 0
    moy_sans = sum(temps_sans_v2x) / len(temps_sans_v2x) if temps_sans_v2x else 0
    diff = moy_sans - moy_avec if (moy_avec and moy_sans) else 0

    return resultats, round(moy_avec, 2), round(moy_sans, 2), round(diff, 2)

@app.route('/')
def index():
    resultats, moy_avec, moy_sans, diff = charger_et_analyser_stats()
    return render_template('index.html', resultats=resultats, moy_avec=moy_avec, moy_sans=moy_sans, diff=diff)

@app.route('/export')
def export_csv():
    if os.path.exists(stats_manager.fichier_csv):
        return send_file(stats_manager.fichier_csv, as_attachment=True, download_name="export_statistiques_v2x.csv")
    return "Aucun fichier CSV disponible.", 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)