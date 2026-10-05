class FeuTricolore:
    def __init__(self, id_voie: str):
        self.__id_voie: str = id_voie
        self.__etat_actuel: str = "Rouge"  # Vert, Orange, Rouge
        self.__duree_cycle_actuel: int = 33
        self.__temps_dans_etat: int = 0

    @property
    def id_voie(self) -> str:
        return self.__id_voie

    @property
    def etat_actuel(self) -> str:
        return self.__etat_actuel

    @etat_actuel.setter
    def etat_actuel(self, nouvel_etat: str) -> None:
        self.__etat_actuel = nouvel_etat

    @property
    def temps_dans_etat(self) -> int:
        return self.__temps_dans_etat

    def incrementer_temps(self) -> None:
        self.__temps_dans_etat += 1

    def changer_etat_normal(self) -> None:
        """Alterne entre Vert, Orange et Rouge selon le temps écoulé."""
        if self.__etat_actuel == "Vert" and self.__temps_dans_etat >= 15:
            self.__etat_actuel = "Orange"
            self.__temps_dans_etat = 0
            print(f"Feu {self.__id_voie} -> ORANGE")
        elif self.__etat_actuel == "Orange" and self.__temps_dans_etat >= 3:
            self.__etat_actuel = "Rouge"
            self.__temps_dans_etat = 0
            print(f"Feu {self.__id_voie} -> ROUGE")
        elif self.__etat_actuel == "Rouge" and self.__temps_dans_etat >= 15:
            self.__etat_actuel = "Vert"
            self.__temps_dans_etat = 0
            print(f"Feu {self.__id_voie} -> VERT")

    def forcer_passage_vert(self) -> None:
        self.__etat_actuel = "Vert"
        self.__temps_dans_etat = 0
        print(f"Feu {self.__id_voie} : Forcé au VERT (Passage d'urgence).")

    def restaurer_cycle_normal(self) -> None:
        self.__etat_actuel = "Rouge"
        self.__temps_dans_etat = 0
        print(f"Feu {self.__id_voie} : Reprise du cycle normal.")