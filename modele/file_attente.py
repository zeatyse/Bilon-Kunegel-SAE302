from typing import List, Optional
from .vehicule import Vehicule


class FileAttente:
    def __init__(self, id_voie: str):
        self.__id_voie: str = id_voie
        self.__vehicules: List[Vehicule] = []

    @property
    def id_voie(self) -> str:
        return self.__id_voie

    @property
    def vehicules(self) -> List[Vehicule]:
        return self.__vehicules

    def ajouter_vehicule(self, vehicule: Vehicule) -> None:
        self.__vehicules.append(vehicule)

    def traiter_passage_vehicule(self, feu_est_vert: bool = True) -> None:
        if not self.__vehicules:
            return

        premier = self.__vehicules[0]

        if not premier.en_mouvement:
            if feu_est_vert:
                premier.tenter_de_demarrer()
            else:
                premier.stopper()
                premier.reinitialiser_reaction()
        else:
            evacue = self.__vehicules.pop(0)
            print(f"  [Carrefour] {evacue.id_vehicule} a terminé sa traversée et quitte le carrefour.")

            if self.__vehicules:
                self.__vehicules[0].reinitialiser_reaction()
                if feu_est_vert:
                    self.__vehicules[0].tenter_de_demarrer()
                else:
                    self.__vehicules[0].stopper()

    def calculer_encombrement(self) -> float:
        return sum(v.longueur_cm for v in self.__vehicules)