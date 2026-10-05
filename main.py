import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modele import Ambulance, Carrefour, Vehicule


def main():
    print("=== CONFIGURATION DE LA SIMULATION ===")
    num_voie = int(input("Choisis la voie de l'ambulance (1, 2, 3 ou 4) : "))
    etat_initial = (
        input("État du feu pour cette voie au départ (Vert/Rouge) : ")
        .strip()
        .capitalize()
    )
    taux_trafic = int(
        input("Choisis le taux de trafic (0, 25, 50, 75 ou 100) : ")
    )

    nb_vehicules_max = 6
    nb_vehicules = round((taux_trafic / 100) * nb_vehicules_max)

    carrefour = Carrefour(dimension_cm=15.0)

    # Reinitialisation des feux au Rouge
    for feu in carrefour.feux:
        feu.etat_actuel = "Rouge"

    # Configuration de la voie sélectionnée
    id_voie_choisie = f"Voie_{num_voie}"
    carrefour.feux[num_voie - 1].etat_actuel = etat_initial

    # Voie transversale au Vert si la voie de l'ambulance est au Rouge au départ
    if etat_initial == "Rouge":
        voie_transversale = 2 if num_voie in [1, 3] else 1
        carrefour.feux[voie_transversale - 1].etat_actuel = "Vert"

    carrefour.initialiser_simulation(taux_trafic=taux_trafic)
    voie_cible = carrefour.voies[num_voie - 1]

    print(f"\n--- Chargement initial de la {id_voie_choisie} (Trafic: {taux_trafic}%) ---")
    for i in range(1, nb_vehicules + 1):
        v = Vehicule(id_vehicule=f"V{i}", longueur_cm=2.0, position_dans_file=i)
        voie_cible.ajouter_vehicule(v)
        print(f"Ajout du véhicule V{i} en position {i}")

    print("\n--- Début du trafic normal (sans ambulance) ---")
    for sec in range(1, 3):
        print(f"\n[Seconde {sec}]")
        carrefour.actualiser_etat()

    print("\n--- ARRIVÉE DE L'AMBULANCE & SIGNAL D'URGENCE ---")
    pos_ambulance = len(voie_cible.vehicules) + 1
    ambulance = Ambulance(
        id_vehicule="AMB1", longueur_cm=2.5, position_dans_file=pos_ambulance
    )
    voie_cible.ajouter_vehicule(ambulance)
    print(f"L'ambulance AMB1 arrive sur la {id_voie_choisie} !")

    # Déclenchement immédiat du protocole V2V et V2I à son arrivée
    vehicules_devant = [
        v for v in voie_cible.vehicules if v.id_vehicule != ambulance.id_vehicule
    ]
    if vehicules_devant:
        ambulance.emettre_signal_v2v(vehicules_devant)
    else:
        print("V2V : Aucun véhicule devant l'ambulance.")

    ambulance.emettre_signal_v2i(carrefour, voie_id=id_voie_choisie)

    print("\n--- Dégagement sous priorité d'urgence ---")
    for sec in range(3, 12):
        print(f"\n[Seconde {sec}]")
        carrefour.actualiser_etat()


if __name__ == "__main__":
    main()