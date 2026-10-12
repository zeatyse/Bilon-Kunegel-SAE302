from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .carrefour import Carrefour


class Vehicule:
    def __init__(self, id_vehicule: str, longueur_cm: float, position_dans_file: int):
        self.__id_vehicule: str = id_vehicule
        self.__longueur_cm: float = longueur_cm
        self.__position_dans_file: int = position_dans_file
        self.__en_mouvement: bool = False
        self.__alerte_v2v: bool = False
        self.__temps_reaction_ecoule: int = 0

    @property
    def id_vehicule(self) -> str:
        return self.__id_vehicule

    @property
    def longueur_cm(self) -> float:
        return self.__longueur_cm

    @property
    def position_dans_file(self) -> int:
        return self.__position_dans_file

    @property
    def en_mouvement(self) -> bool:
        return self.__en_mouvement

    @property
    def alerte_v2v(self) -> bool:
        return self.__alerte_v2v

    def avancer(self) -> None:
        self.__en_mouvement = True
        print(f"Véhicule {self.__id_vehicule} avance.")

    def stopper(self) -> None:
        self.__en_mouvement = False
        print(f"Véhicule {self.__id_vehicule} est à l'arrêt.")

    def recevoir_alerte_v2v(self) -> None:
        self.__alerte_v2v = True
        print(f"V2V: Véhicule {self.__id_vehicule} a reçu l'alerte d'urgence (réaction accélérée à 1s).")

    def tenter_de_demarrer(self) -> bool:
        """Gère le temps de réaction : 1 seconde si V2V actif, 2 secondes sinon.
        Renvoie True si le véhicule commence enfin à avancer."""
        delai_requis = 1 if self.__alerte_v2v else 2

        self.__temps_reaction_ecoule += 1
        if self.__temps_reaction_ecoule >= delai_requis:
            self.avancer()
            return True
        else:
            print(
                f"Véhicule {self.__id_vehicule} réagit (temps écoulé : {self.__temps_reaction_ecoule}/{delai_requis}s)...")
            return False

    def reinitialiser_reaction(self) -> None:
        self.__temps_reaction_ecoule = 0


class Ambulance(Vehicule):
    def __init__(self, id_vehicule: str, longueur_cm: float, position_dans_file: int):
        super().__init__(id_vehicule, longueur_cm, position_dans_file)
        self.__sirene_active: bool = False
        self.__signal_v2i_envoye: bool = False

    @property
    def sirene_active(self) -> bool:
        return self.__sirene_active

    @property
    def signal_v2i_envoye(self) -> bool:
        return self.__signal_v2i_envoye

    def emettre_signal_v2i(self, carrefour: "Carrefour", voie_id: str) -> None:
        self.__sirene_active = True
        self.__signal_v2i_envoye = True
        print(f"V2I: Ambulance {self.id_vehicule} émet un signal de priorité au carrefour (Voie: {voie_id}).")
        carrefour.recevoir_signal_v2i(voie_id)

    def emettre_signal_v2v(self, voisins: List[Vehicule]) -> None:
        print(f"V2V: Ambulance {self.id_vehicule} émet une alerte aux véhicules en amont.")
        for vehicule in voisins:
            if vehicule.id_vehicule != self.id_vehicule:
                vehicule.recevoir_alerte_v2v()