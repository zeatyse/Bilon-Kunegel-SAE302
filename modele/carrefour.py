from typing import List
from .feu_tricolore import FeuTricolore
from .file_attente import FileAttente


class Carrefour:
    def __init__(self, dimension_cm: float = 15.0):
        self.__dimension_cm: float = dimension_cm
        noms_voies = ["Voie A", "Voie B", "Voie C", "Voie D"]

        self.__feux: List[FeuTricolore] = [FeuTricolore(nom) for nom in noms_voies]
        self.__voies: List[FileAttente] = [FileAttente(nom) for nom in noms_voies]
        self.__mode_urgence_active: bool = False

        # Initialisation synchronisée des paires
        self.__feux[0].etat_actuel = "Vert"  # Voie A
        self.__feux[2].etat_actuel = "Vert"  # Voie C
        self.__feux[1].etat_actuel = "Rouge"  # Voie B
        self.__feux[3].etat_actuel = "Rouge"  # Voie D

    @property
    def dimension_cm(self) -> float:
        return self.__dimension_cm

    @property
    def feux(self) -> List[FeuTricolore]:
        return self.__feux

    @property
    def voies(self) -> List[FileAttente]:
        return self.__voies

    @property
    def mode_urgence_active(self) -> bool:
        return self.__mode_urgence_active

    def initialiser_simulation(self, taux_trafic: int) -> None:
        print(f"Initialisation du carrefour {self.__dimension_cm}x{self.__dimension_cm} cm (Trafic: {taux_trafic}%).")

    def actualiser_etat(self) -> None:
        """Cadence le passage du temps et adapte le mouvement des voitures."""
        if not self.__mode_urgence_active:
            for feu in self.__feux:
                feu.incrementer_temps()
                feu.changer_etat_normal()

        for feu, voie in zip(self.__feux, self.__voies):
            if feu.etat_actuel == "Vert":
                voie.traiter_passage_vehicule()
            else:  # Rouge ou Orange = arrêt
                for v in voie.vehicules:
                    v.stopper()

    def recevoir_signal_v2i(self, voie_id: str) -> None:
        self.__mode_urgence_active = True
        print(f"\n[URGENCE] Carrefour : Prise en charge du signal V2I pour la {voie_id}.")
        for feu in self.__feux:
            if feu.id_voie == voie_id:
                feu.forcer_passage_vert()
            else:
                feu.etat_actuel = "Rouge"

    def reinitialiser_trafic(self, voie_urgence: str) -> None:
        self.__mode_urgence_active = False
        print("\n[NORMAL] Reprise du trafic régulier : Activation des voies transversales.")

        # Si l'ambulance venait de A ou C, on donne le Vert à B et D
        if voie_urgence in ["Voie A", "Voie C"]:
            voies_vertes = ["Voie B", "Voie D"]
        else:
            voies_vertes = ["Voie A", "Voie C"]

        for feu in self.__feux:
            if feu.id_voie in voies_vertes:
                feu.forcer_reprise("Vert")
            else:
                feu.forcer_reprise("Rouge")