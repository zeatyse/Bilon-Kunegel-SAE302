import os
import sys
from flask import Flask, render_template, send_file

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from modele.gestionnaire_stats import GestionnaireStats, CONFIGS_V2X

app = Flask(__name__)
stats_manager = GestionnaireStats()


@app.route('/')
def index():
    try:
        resultats = stats_manager.recuperer_resultats()
        scenarios = stats_manager.moyennes_par_scenario(resultats)

        gains = [s['gain'] for s in scenarios if s['gain'] is not None]
        gain_moyen = round(sum(gains) / len(gains), 2) if gains else None

        return render_template(
            'index.html',
            resultats=resultats,
            scenarios=scenarios,
            configs=CONFIGS_V2X,
            gain_moyen=gain_moyen,
            nb_comparables=len(gains),
        )
    except Exception as e:
        app.logger.exception("Erreur lors du chargement du tableau de bord : %s", e)
        return "Erreur interne du serveur.", 500


@app.route('/export')
def export_csv():
    if os.path.exists(stats_manager.fichier_csv):
        return send_file(stats_manager.fichier_csv, as_attachment=True, download_name="export_statistiques_v2x.csv")
    return "Aucun fichier CSV disponible.", 404


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=False)
