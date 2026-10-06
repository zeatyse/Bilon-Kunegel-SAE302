import os
import sys

# Ajoute le dossier courant au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from modele import Ambulance, Carrefour, Vehicule


def main():
    print("=== CONFIGURATION DE LA SIMULATION ===")

    while True:
        choix_amb = input("Présence d'une ambulance ? (1 = Oui, 0 = Non) : ")
        if choix_amb == "1":
            avec_ambulance = True
            break
        elif choix_amb == "0":
            avec_ambulance = False
            break
        else:
            print("Erreur : Entrez 1 pour Oui, ou 0 pour Non.")

    while True:
        choix_voie = input("Choisis la voie de l'ambulance ou principale (A, B, C ou D) : ")
        choix_lettre = choix_voie.upper()
        if choix_lettre in ["A", "B", "C", "D"]:
            num_voie = ["A", "B", "C", "D"].index(choix_lettre) + 1
            break
        else:
            print("Erreur : Entrez A, B, C ou D.")

    while True:
        choix_feu = input(f"État du feu pour la Voie {choix_lettre} au départ (V = Vert, R = Rouge) : ")
        if choix_feu.upper() == "V":
            etat_initial = "Vert"
            break
        elif choix_feu.upper() == "R":
            etat_initial = "Rouge"
            break
        else:
            print("Erreur : Entrez V pour Vert, ou R pour Rouge.")

    while True:
        choix_trafic = input("Niveau de trafic (0=0%, 1=25%, 2=50%, 3=75%, 4=100%) : ")
        if choix_trafic in ["0", "1", "2", "3", "4"]:
            taux_trafic = int(choix_trafic) * 25
            break
        else:
            print("Erreur : Entrez un chiffre entre 0 et 4.")

    nb_vehicules_max = 6
    nb_vehicules = int((taux_trafic / 100) * nb_vehicules_max)

    carrefour = Carrefour(dimension_cm=15.0)

    # Initialisation des feux selon la voie choisie
    if num_voie in [1, 3]:  # Voies A et C
        if etat_initial == "Vert":
            carrefour.feux[0].etat_actuel = "Vert"
            carrefour.feux[2].etat_actuel = "Vert"
            carrefour.feux[1].etat_actuel = "Rouge"
            carrefour.feux[3].etat_actuel = "Rouge"
        else:
            carrefour.feux[0].etat_actuel = "Rouge"
            carrefour.feux[2].etat_actuel = "Rouge"
            carrefour.feux[1].etat_actuel = "Vert"
            carrefour.feux[3].etat_actuel = "Vert"
    else:  # Voies B et D
        if etat_initial == "Vert":
            carrefour.feux[1].etat_actuel = "Vert"
            carrefour.feux[3].etat_actuel = "Vert"
            carrefour.feux[0].etat_actuel = "Rouge"
            carrefour.feux[2].etat_actuel = "Rouge"
        else:
            carrefour.feux[1].etat_actuel = "Rouge"
            carrefour.feux[3].etat_actuel = "Rouge"
            carrefour.feux[0].etat_actuel = "Vert"
            carrefour.feux[2].etat_actuel = "Vert"

    carrefour.initialiser_simulation(taux_trafic=taux_trafic)
    id_voie_choisie = f"Voie {choix_lettre}"
    voie_cible = carrefour.voies[num_voie - 1]

    lettres = ["A", "B", "C", "D"]
    print(f"\n--- Chargement initial de toutes les voies (Trafic: {taux_trafic}%) ---")

    for idx, voie in enumerate(carrefour.voies):
        lettre = lettres[idx]
        for i in range(1, nb_vehicules + 1):
            v = Vehicule(id_vehicule=f"V_{lettre}{i}", longueur_cm=2.0, position_dans_file=i)
            voie.ajouter_vehicule(v)
            print(f"Voie {lettre} : ajout du véhicule V_{lettre}{i}")

    if avec_ambulance:
        print("\n--- Début du trafic normal (sans ambulance pendant 2s) ---")
        for sec in range(1, 3):
            print(f"\n[Seconde {sec}]")
            carrefour.actualiser_etat()

        print("\n--- ARRIVÉE DE L'AMBULANCE & SIGNAL D'URGENCE ---")
        pos_ambulance = len(voie_cible.vehicules) + 1
        ambulance = Ambulance(id_vehicule="AMB1", longueur_cm=2.5, position_dans_file=pos_ambulance)
        voie_cible.ajouter_vehicule(ambulance)
        print(f"L'ambulance AMB1 arrive sur la {id_voie_choisie} !")

        vehicules_devant = [v for v in voie_cible.vehicules if v.id_vehicule != ambulance.id_vehicule]

        if vehicules_devant:
            ambulance.emettre_signal_v2v(vehicules_devant)
        else:
            print("V2V : Aucun véhicule devant l'ambulance.")

        ambulance.emettre_signal_v2i(carrefour, voie_id=id_voie_choisie)

        print("\n--- Dégagement sous priorité d'urgence ---")
        ambulance_passee = False
        compteur_reprise = 0

        for sec in range(3, 20):
            print(f"\n[Seconde {sec}]")
            carrefour.actualiser_etat()

            if carrefour.mode_urgence_active:
                ambulance_presente = any(v.id_vehicule == "AMB1" for v in voie_cible.vehicules)

                if not ambulance_presente and not ambulance_passee:
                    print("  -> [INFO] L'ambulance a quitté le carrefour ! Le trafic reprend dans 2 secondes...")
                    ambulance_passee = True

                if ambulance_passee:
                    compteur_reprise += 1
                    if compteur_reprise == 2:
                        carrefour.reinitialiser_trafic(id_voie_choisie)

    else:
        print("\n--- Début du trafic normal ---")
        for sec in range(1, 13):
            print(f"\n[Seconde {sec}]")
            carrefour.actualiser_etat()


if __name__ == "__main__":
    main()