import tkinter as tk
from tkinter import ttk
import threading
import time
import sys
import os

# Ajoute le dossier courant et parent au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from modele.carrefour import Carrefour
from modele.vehicule import Vehicule, Ambulance
from modele.gestionnaire_stats import GestionnaireStats  

class SimulateurGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulation V2X - SAE302")
        self.root.geometry("1200x800")

        self.chrono_amb_sec = 0.0
        self.chrono_actif = False
        self.clignotement_actif = False
        self.clignotement_couleur = "coral"
        self.simulation_en_cours = False  # Contrôle d'arrêt

        self.directions_vehicules = {}
        self.delais_reaction = {0: 0, 1: 0, 2: 0, 3: 0}  # Moteur de réaction

        # Initialisation du gestionnaire de stats (CSV / MariaDB)
        self.stats_manager = GestionnaireStats()

        # --- Panneau de configuration (Gauche) ---
        self.frame_config = tk.Frame(root, width=350, padx=10, pady=10)
        self.frame_config.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(self.frame_config, text="=== CONFIGURATION ===", font=("Arial", 12, "bold")).pack(pady=10)

        tk.Label(self.frame_config, text="Voie du véhicule test :").pack()
        self.liste_voies = ["A", "B", "C", "D"]
        self.var_voie = tk.StringVar(value="A")
        ttk.Combobox(self.frame_config, textvariable=self.var_voie, values=self.liste_voies, state="readonly").pack(
            pady=5)

        tk.Label(self.frame_config, text="État initial de cette voie :").pack()
        self.var_etat = tk.StringVar(value="Rouge")
        ttk.Combobox(self.frame_config, textvariable=self.var_etat, values=["Vert", "Rouge"], state="readonly").pack(
            pady=5)

        tk.Label(self.frame_config, text="Taux de trafic global (%) :").pack()
        self.var_trafic = tk.IntVar(value=100)
        ttk.Combobox(self.frame_config, textvariable=self.var_trafic, values=[0, 25, 50, 75, 100],
                     state="readonly").pack(pady=5)

        tk.Label(self.frame_config, text="Trajectoire de l'Ambulance :").pack()
        self.var_direction = tk.StringVar(value="Tout droit")
        ttk.Combobox(self.frame_config, textvariable=self.var_direction,
                     values=["Tout droit", "Tourner à Droite", "Tourner à Gauche"], state="readonly").pack(pady=5)

        # --- Options V2X Granulaires (V2I et V2V) ---
        tk.Label(self.frame_config, text="Options de communication V2X :", font=("Arial", 10, "bold")).pack(
            pady=(10, 5))

        self.var_v2i = tk.BooleanVar(value=True)
        self.btn_v2i = tk.Checkbutton(
            self.frame_config,
            text="Activer V2I (Feux prioritaires)",
            variable=self.var_v2i,
            font=("Arial", 9, "bold"),
            fg="red"
        )
        self.btn_v2i.pack(anchor=tk.W, padx=20, pady=2)

        self.var_v2v = tk.BooleanVar(value=True)
        self.btn_v2v = tk.Checkbutton(
            self.frame_config,
            text="Activer V2V (Alerte véhicules amont)",
            variable=self.var_v2v,
            font=("Arial", 9, "bold"),
            fg="#ff8c00"
        )
        self.btn_v2v.pack(anchor=tk.W, padx=20, pady=2)

        # Boutons Lancer / Arrêter
        self.btn_start = tk.Button(self.frame_config, text="Lancer la simulation", bg="green", fg="white",
                                   font=("Arial", 10, "bold"), command=self.lancer_thread)
        self.btn_start.pack(pady=10)

        self.btn_stop = tk.Button(self.frame_config, text="Arrêter la simulation", bg="darkred", fg="white",
                                  font=("Arial", 10, "bold"), command=self.arreter_simulation, state=tk.DISABLED)
        self.btn_stop.pack(pady=5)

        tk.Label(self.frame_config, text="Journal des événements :").pack(pady=(10, 0))
        self.log_text = tk.Text(self.frame_config, height=15, width=40, state=tk.DISABLED, bg="#f4f4f4")
        self.log_text.pack(fill=tk.Y, expand=True)

        # --- Panneau Visuel (Droite) ---
        self.frame_visuel = tk.Frame(root, bg="#d9d9d9")
        self.frame_visuel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.frame_visuel, width=800, height=800, bg="#e8e8e8")
        self.canvas.pack(pady=10)

        self.dessiner_carrefour()
        self.animer_clignotement()

    def arreter_simulation(self):
        self.simulation_en_cours = False
        self.btn_stop.config(state=tk.DISABLED)

    def dessiner_un_feu(self, direction):
        if direction == "A":
            self.canvas.create_oval(330, 460, 340, 470, fill="#777777", outline="black", tags="feu")
            self.canvas.create_line(335, 465, 335, 425, fill="#444444", width=4, tags="feu")
            self.canvas.create_rectangle(327, 405, 343, 445, fill="#222222", outline="black", width=2, tags="feu")
            self.canvas.create_line(327, 425, 343, 425, fill="#555555", width=2, tags="feu")
            id_rouge = self.canvas.create_oval(322, 410, 332, 420, fill="#4a0000", outline="black", tags="feu")
            id_vert = self.canvas.create_oval(322, 430, 332, 440, fill="#004a00", outline="black", tags="feu")
        elif direction == "B":
            self.canvas.create_oval(330, 330, 340, 340, fill="#777777", outline="black", tags="feu")
            self.canvas.create_line(335, 335, 375, 335, fill="#444444", width=4, tags="feu")
            self.canvas.create_rectangle(355, 327, 395, 343, fill="#222222", outline="black", width=2, tags="feu")
            self.canvas.create_line(375, 327, 375, 343, fill="#555555", width=2, tags="feu")
            id_rouge = self.canvas.create_oval(360, 322, 370, 332, fill="#4a0000", outline="black", tags="feu")
            id_vert = self.canvas.create_oval(380, 322, 390, 332, fill="#004a00", outline="black", tags="feu")
        elif direction == "C":
            self.canvas.create_oval(460, 330, 470, 340, fill="#777777", outline="black", tags="feu")
            self.canvas.create_line(465, 335, 465, 375, fill="#444444", width=4, tags="feu")
            self.canvas.create_rectangle(457, 355, 473, 395, fill="#222222", outline="black", width=2, tags="feu")
            self.canvas.create_line(457, 375, 473, 375, fill="#555555", width=2, tags="feu")
            id_rouge = self.canvas.create_oval(468, 380, 478, 390, fill="#4a0000", outline="black", tags="feu")
            id_vert = self.canvas.create_oval(468, 360, 478, 370, fill="#004a00", outline="black", tags="feu")
        elif direction == "D":
            self.canvas.create_oval(460, 460, 470, 470, fill="#777777", outline="black", tags="feu")
            self.canvas.create_line(465, 465, 425, 465, fill="#444444", width=4, tags="feu")
            self.canvas.create_rectangle(405, 457, 445, 473, fill="#222222", outline="black", width=2, tags="feu")
            self.canvas.create_line(425, 457, 425, 473, fill="#555555", width=2, tags="feu")
            id_rouge = self.canvas.create_oval(430, 468, 440, 478, fill="#4a0000", outline="black", tags="feu")
            id_vert = self.canvas.create_oval(410, 468, 420, 478, fill="#004a00", outline="black", tags="feu")

        return id_rouge, id_vert

    def dessiner_carrefour(self):
        self.canvas.create_rectangle(350, 0, 450, 800, fill="#555555", outline="")
        self.canvas.create_rectangle(0, 350, 800, 450, fill="#555555", outline="")
        self.canvas.create_rectangle(350, 350, 450, 450, fill="#666666", outline="")

        self.canvas.create_line(400, 0, 400, 350, fill="white", dash=(10, 10))
        self.canvas.create_line(400, 450, 400, 800, fill="white", dash=(10, 10))
        self.canvas.create_line(0, 400, 350, 400, fill="white", dash=(10, 10))
        self.canvas.create_line(450, 400, 800, 400, fill="white", dash=(10, 10))

        self.canvas.create_text(150, 375, text="A", font=("Arial", 40, "bold"), fill="white")
        self.canvas.create_text(425, 150, text="B", font=("Arial", 40, "bold"), fill="white")
        self.canvas.create_text(650, 425, text="C", font=("Arial", 40, "bold"), fill="white")
        self.canvas.create_text(375, 650, text="D", font=("Arial", 40, "bold"), fill="white")

        self.feux_ui = {
            0: self.dessiner_un_feu("A"),
            1: self.dessiner_un_feu("B"),
            2: self.dessiner_un_feu("C"),
            3: self.dessiner_un_feu("D")
        }

        self.chrono_amb_ui = self.canvas.create_text(150, 50, text="Chronomètre : 0.00s", font=("Arial", 20, "bold"),
                                                     fill="blue")

        # Légende
        self.canvas.create_rectangle(20, 750, 50, 780, fill="#f0f0f0", outline="black")
        self.canvas.create_rectangle(25, 755, 45, 775, fill="coral", outline="black", tags="legende_clignotante")
        self.canvas.create_text(60, 765, text="= Prévenu du danger (V2V)", anchor=tk.W, font=("Arial", 16, "bold"),
                                fill="black")

    def animer_clignotement(self):
        if self.clignotement_actif:
            self.clignotement_couleur = "orange" if self.clignotement_couleur == "coral" else "coral"
            self.canvas.itemconfig("averti", fill=self.clignotement_couleur)
            self.canvas.itemconfig("legende_clignotante", fill=self.clignotement_couleur)
        else:
            self.canvas.itemconfig("legende_clignotante", fill="lightgrey")

        self.root.after(700, self.animer_clignotement)

    def maj_chrono_amb(self):
        self.canvas.itemconfig(self.chrono_amb_ui, text=f"Chronomètre : {self.chrono_amb_sec:.2f}s")

    def ecrire_log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def actualiser_feu_ui(self, index_voie, etat):
        id_rouge, id_vert = self.feux_ui[index_voie]
        if etat.lower() == "vert":
            self.canvas.itemconfig(id_rouge, fill="#4a0000")
            self.canvas.itemconfig(id_vert, fill="#00FF00")
        else:
            self.canvas.itemconfig(id_rouge, fill="#FF0000")
            self.canvas.itemconfig(id_vert, fill="#004a00")

    def get_trajectoire(self, idx, direction):
        if idx == 0:
            if direction == "Tourner à Droite":
                return 375, 485, 0, 130
            elif direction == "Tourner à Gauche":
                return 425, 315, 0, -130
            else:
                return 445, 425, 130, 0
        elif idx == 1:
            if direction == "Tourner à Droite":
                return 315, 375, -130, 0
            elif direction == "Tourner à Gauche":
                return 485, 425, 130, 0
            else:
                return 375, 445, 0, 130
        elif idx == 2:
            if direction == "Tourner à Droite":
                return 425, 315, 0, -130
            elif direction == "Tourner à Gauche":
                return 375, 485, 0, 130
            else:
                return 355, 375, -130, 0
        elif idx == 3:
            if direction == "Tourner à Droite":
                return 485, 425, 130, 0
            elif direction == "Tourner à Gauche":
                return 315, 375, -130, 0
            else:
                return 425, 355, 0, -130

    def actualiser_tous_vehicules_ui(self, carrefour, index_voie_test, pos_ambulance, vehicules_positions):
        self.canvas.delete("vehicule")

        coords = {
            0: (315, 425, -45, 0),
            1: (375, 315, 0, -45),
            2: (485, 375, 45, 0),
            3: (425, 485, 0, 45)
        }

        for idx in range(4):
            x_base, y_base, dx_wait, dy_wait = coords[idx]

            for k, pos_logique in enumerate(vehicules_positions[idx]):
                i = k + 1

                if idx == index_voie_test and pos_ambulance and i == pos_ambulance:
                    v_id = "AMB1"
                else:
                    v_id = f"V_{self.liste_voies[idx]}{i}"

                direction = self.directions_vehicules.get(v_id, "Tout droit")

                if pos_logique > 1:
                    x = x_base + (pos_logique - 1) * dx_wait
                    y = y_base + (pos_logique - 1) * dy_wait
                else:
                    x_mid, y_mid, dx_out, dy_out = self.get_trajectoire(idx, direction)

                    if pos_logique >= 0:
                        t = 1.0 - pos_logique

                        if direction == "Tout droit":
                            x = x_base + t * (x_mid - x_base)
                            y = y_base + t * (y_mid - y_base)
                        else:
                            if idx == 0:
                                cx, cy = (375 if direction == "Tourner à Droite" else 425), 425
                            elif idx == 1:
                                cx, cy = 375, (375 if direction == "Tourner à Droite" else 425)
                            elif idx == 2:
                                cx, cy = (425 if direction == "Tourner à Droite" else 375), 375
                            elif idx == 3:
                                cx, cy = 425, (425 if direction == "Tourner à Droite" else 375)

                            x = ((1.0 - t) ** 2) * x_base + 2 * (1.0 - t) * t * cx + (t ** 2) * x_mid
                            y = ((1.0 - t) ** 2) * y_base + 2 * (1.0 - t) * t * cy + (t ** 2) * y_mid
                    else:
                        distance_out = abs(pos_logique)
                        x = x_mid + distance_out * dx_out
                        y = y_mid + distance_out * dy_out

                if not (-30 < x < 830 and -30 < y < 830):
                    continue

                tags_vehicule = ["vehicule"]

                if v_id == "AMB1":
                    emoji = "🚑"
                    label = "AMB"
                    couleur = "#87CEFA"
                    averti = False
                else:
                    emoji = "🚗"
                    label = f"{self.liste_voies[idx]}{i}"
                    couleur = "#FFD700"
                    averti = self.clignotement_actif and idx == index_voie_test and pos_ambulance and i < pos_ambulance

                if averti:
                    tags_vehicule.append("averti")
                    couleur = self.clignotement_couleur

                # 1. Le fond de couleur
                self.canvas.create_rectangle(x - 16, y - 16, x + 16, y + 16, fill=couleur, outline="black",
                                             tags=tuple(tags_vehicule))
                # 2. L'emoji par-dessus
                self.canvas.create_text(x, y - 3, text=emoji, font=("Arial", 18), tags=tuple(tags_vehicule))

                # Compte à rebours du temps de réaction directement sur la voiture de tête
                if i == 1 and self.delais_reaction[idx] > 0 and carrefour.feux[idx].etat_actuel == "Vert":
                    self.canvas.create_text(x, y - 30, text=f"⏱️ {self.delais_reaction[idx] * 0.05:.1f}s",
                                            font=("Arial", 9, "bold"), fill="red", tags="vehicule")

                # 3. Label de nom
                self.canvas.create_text(x, y + 15, text=label, font=("Arial", 8, "bold"), fill="black", tags="vehicule")

        self.canvas.tag_raise("feu")

    def lancer_thread(self):
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.btn_v2i.config(state=tk.DISABLED)
        self.btn_v2v.config(state=tk.DISABLED)
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

        self.simulation_en_cours = True
        threading.Thread(target=self.executer_simulation, daemon=True).start()

    def executer_simulation(self):
        self.chrono_amb_sec = 0.0
        self.chrono_actif = True
        self.clignotement_actif = False
        pos_ambulance = None
        self.directions_vehicules.clear()

        # Initialisation propre des temps de réaction
        self.delais_reaction = {0: 0, 1: 0, 2: 0, 3: 0}

        self.root.after(0, self.maj_chrono_amb)

        index_voie = self.liste_voies.index(self.var_voie.get())
        etat_initial = self.var_etat.get()
        taux_trafic = self.var_trafic.get()

        v2i_actif = self.var_v2i.get()
        v2v_actif = self.var_v2v.get()

        direction_ambulance = self.var_direction.get()

        nb_vehicules = int((taux_trafic / 100) * 6)

        vehicules_positions = {
            0: [float(i) for i in range(1, nb_vehicules + 1)],
            1: [float(i) for i in range(1, nb_vehicules + 1)],
            2: [float(i) for i in range(1, nb_vehicules + 1)],
            3: [float(i) for i in range(1, nb_vehicules + 1)]
        }

        self.ecrire_log(f"=== INITIALISATION GLOBALE ===")
        carrefour = Carrefour(dimension_cm=15.0)

        etats = {}
        if index_voie in [0, 2]:
            etats = {0: etat_initial, 2: etat_initial, 1: "Rouge" if etat_initial == "Vert" else "Vert",
                     3: "Rouge" if etat_initial == "Vert" else "Vert"}
        else:
            etats = {1: etat_initial, 3: etat_initial, 0: "Rouge" if etat_initial == "Vert" else "Vert",
                     2: "Rouge" if etat_initial == "Vert" else "Vert"}

        # On surveille les états pour détecter les transitions Rouge ➜ Vert
        feux_etats_precedents = {i: "Rouge" for i in range(4)}

        for i, etat in etats.items():
            carrefour.feux[i].etat_actuel = etat
            feux_etats_precedents[i] = etat
            self.root.after(0, self.actualiser_feu_ui, i, etat)

        carrefour.initialiser_simulation(taux_trafic=taux_trafic)

        self.ecrire_log(f"Trafic généré ({taux_trafic}%) sur toutes les voies.")
        for idx in range(4):
            lettre = self.liste_voies[idx]
            for i in range(1, nb_vehicules + 1):
                v_id = f"V_{lettre}{i}"
                v = Vehicule(id_vehicule=v_id, longueur_cm=2.0, position_dans_file=i)
                carrefour.voies[idx].ajouter_vehicule(v)
                self.directions_vehicules[v_id] = "Tout droit"

        self.root.after(0, self.actualiser_tous_vehicules_ui, carrefour, index_voie, None, vehicules_positions)

        def animer_tick():
            for idx in range(4):
                feu_vert = carrefour.feux[idx].etat_actuel == "Vert"
                etat_precedent = feux_etats_precedents[idx]

                # Si le feu passe du Rouge au Vert, on déclenche le délai de démarrage
                if feu_vert and etat_precedent == "Rouge":
                    # Pour la voie test (contenant l'ambulance), le délai s'ajuste selon la présence d'alerte V2V
                    if idx == index_voie:
                        self.delais_reaction[idx] = 20 if v2v_actif else 40
                        temps_attente = self.delais_reaction[idx] * 0.05
                        self.ecrire_log(
                            f"-> [TRANSITION FEU VERT] Réaction {self.liste_voies[idx]}: {temps_attente:.1f}s (alerte V2V active)" if v2v_actif else f"-> [TRANSITION FEU VERT] Réaction {self.liste_voies[idx]}: {temps_attente:.1f}s (sans alerte V2V)")
                    else:
                        # Délai classique de 2 secondes pour les autres voies non alertées
                        self.delais_reaction[idx] = 40

                feux_etats_precedents[idx] = carrefour.feux[idx].etat_actuel

                # On réduit le délai de réaction au passage du temps (1 tick = 0.05s)
                if feu_vert and self.delais_reaction[idx] > 0:
                    self.delais_reaction[idx] -= 1

                for k in range(len(vehicules_positions[idx])):
                    pos = vehicules_positions[idx][k]
                    peut_avancer = feu_vert and (self.delais_reaction[idx] <= 0)

                    if k == 0:
                        cible = -100.0 if (peut_avancer or pos < 0.95) else 1.0
                    else:
                        pos_precedente = vehicules_positions[idx][k - 1]
                        if pos < 0.95:
                            cible = pos_precedente + 1.0
                        else:
                            if peut_avancer:
                                cible = pos_precedente + 1.0
                            else:
                                cible = max(1.0, pos_precedente + 1.0)

                    # --- NOUVEAU FIX: CÉDEZ-LE-PASSAGE (Eviter l'accident de face) ---
                    est_ambulance = (pos_ambulance is not None) and (idx == index_voie) and (k == pos_ambulance - 1)
                    if est_ambulance and direction_ambulance == "Tourner à Gauche" and pos > 0.4:
                        idx_en_face = (idx + 2) % 4
                        # Si le feu en face est vert, on doit vérifier s'il y a du monde
                        if carrefour.feux[idx_en_face].etat_actuel == "Vert":
                            for pos_en_face in vehicules_positions[idx_en_face]:
                                # Si un véhicule arrive en face et est proche du carrefour
                                if -0.2 < pos_en_face < 2.5:
                                    cible = max(0.6, cible)  # L'ambulance s'arrête au milieu et cède le passage !
                                    break

                    if pos > cible:
                        step = 0.075 if est_ambulance else 0.05

                        vehicules_positions[idx][k] -= step
                        if vehicules_positions[idx][k] < cible:
                            vehicules_positions[idx][k] = cible

            self.root.after(0, self.actualiser_tous_vehicules_ui, carrefour, index_voie, pos_ambulance,
                            vehicules_positions)

        ticks_ecoules = 0
        self.ecrire_log("\n--- Trafic normal (2 secondes) ---")

        for _ in range(40):
            if not self.simulation_en_cours: break
            time.sleep(0.05)
            ticks_ecoules += 1
            if self.chrono_actif:
                self.chrono_amb_sec += 0.05
                self.root.after(0, self.maj_chrono_amb)
            animer_tick()

        if self.simulation_en_cours:
            ambulance_passee_carrefour = False
            compteur_reprise = 0
            id_voie_choisie = f"Voie {self.liste_voies[index_voie]}"

            self.ecrire_log(f"\n--- ARRIVÉE DU VÉHICULE TEST ({id_voie_choisie}) ---")
            pos_ambulance = len(carrefour.voies[index_voie].vehicules) + 1
            ambulance = Ambulance(id_vehicule="AMB1", longueur_cm=2.5, position_dans_file=pos_ambulance)
            carrefour.voies[index_voie].ajouter_vehicule(ambulance)

            self.directions_vehicules["AMB1"] = direction_ambulance
            vehicules_positions[index_voie].append(float(pos_ambulance) + 2.0)

            # --- Gestion V2V ---
            if v2v_actif:
                self.clignotement_actif = True
                vehicules_devant = [v for v in carrefour.voies[index_voie].vehicules if v.id_vehicule != "AMB1"]
                if vehicules_devant:
                    ambulance.emettre_signal_v2v(vehicules_devant)
                    self.ecrire_log("V2V : Alerte transmise aux véhicules en amont (clignotement activé).")
                else:
                    self.ecrire_log("V2V : Aucun véhicule devant l'ambulance.")
            else:
                self.ecrire_log("V2V : Désactivé (pas d'alerte amont).")

            # --- Gestion V2I & Forçage du Feu ---
            if v2i_actif:
                ambulance.emettre_signal_v2i(carrefour, voie_id=id_voie_choisie)
                idx_en_face = (index_voie + 2) % 4

                if direction_ambulance == "Tourner à Gauche":
                    self.ecrire_log(
                        "V2I (Tourner à Gauche) : Sécurisation totale, tous les autres feux passent au ROUGE.")
                    for i in range(4):
                        etat = "Vert" if i == index_voie else "Rouge"
                        carrefour.feux[i].etat_actuel = etat
                        self.root.after(0, self.actualiser_feu_ui, i, etat)
                else:
                    self.ecrire_log(
                        f"V2I ({direction_ambulance}) : La voie de l'ambulance et celle d'en face sont Vertes.")
                    for i in range(4):
                        if i == index_voie or i == idx_en_face:
                            etat = "Vert"
                        else:
                            etat = "Rouge"
                        carrefour.feux[i].etat_actuel = etat
                        self.root.after(0, self.actualiser_feu_ui, i, etat)
            else:
                self.ecrire_log("V2I : Désactivé (les feux suivent leur cycle normal sans priorité).")

        def simulation_active():
            for idx in range(4):
                if vehicules_positions[idx] and vehicules_positions[idx][-1] > -3.5:
                    return True
            return False

        while simulation_active() and self.simulation_en_cours:
            time.sleep(0.05)
            ticks_ecoules += 1

            if self.chrono_actif:
                self.chrono_amb_sec += 0.05
                self.root.after(0, self.maj_chrono_amb)

                if vehicules_positions[index_voie][pos_ambulance - 1] < -3.0:
                    self.chrono_actif = False
                    temps_final = self.chrono_amb_sec
                    self.ecrire_log(f"-> [INFO] Temps total du véhicule : {temps_final:.2f}s")

                    # --- ENREGISTREMENT AUTOMATIQUE DES STATS (CSV) ---
                    self.stats_manager.enregistrer_resultat(
                        taux_trafic=taux_trafic,
                        direction=direction_ambulance,
                        v2i=v2i_actif,
                        v2v=v2v_actif,
                        temps_ambulance=temps_final
                    )

            # Reprise du trafic uniquement si V2I était actif
            if ticks_ecoules % 20 == 0:
                if v2i_actif and getattr(carrefour, 'mode_urgence_active', False):
                    if not ambulance_passee_carrefour and vehicules_positions[index_voie][pos_ambulance - 1] < 0.0:
                        ambulance_passee_carrefour = True
                        self.clignotement_actif = False

                    if ambulance_passee_carrefour:
                        compteur_reprise += 1
                        if compteur_reprise == 2:
                            self.ecrire_log("Reprise du cycle normal des feux tricolores.")
                            carrefour.reinitialiser_trafic(id_voie_choisie)

                            # --- FIX SYNCHRONISATION VISUELLE ET CYCLE ---
                            for i in range(4):
                                self.root.after(0, self.actualiser_feu_ui, i, carrefour.feux[i].etat_actuel)

                            ticks_ecoules = 1

            if not getattr(carrefour, 'mode_urgence_active', False) and ticks_ecoules % 100 == 0:
                for idx in range(4):
                    nouveau_etat = "Vert" if carrefour.feux[idx].etat_actuel == "Rouge" else "Rouge"
                    carrefour.feux[idx].etat_actuel = nouveau_etat
                    self.root.after(0, self.actualiser_feu_ui, idx, nouveau_etat)

            animer_tick()

        if not self.simulation_en_cours:
            self.ecrire_log("\n[!] Simulation interrompue par l'utilisateur.")
        else:
            self.ecrire_log("\n=== FIN DE SIMULATION ===")

        self.clignotement_actif = False

        self.root.after(0, lambda: self.btn_start.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.btn_v2i.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.btn_v2v.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.btn_stop.config(state=tk.DISABLED))


if __name__ == "__main__":
    app = tk.Tk()
    gui = SimulateurGUI(app)
    app.mainloop()
