import subprocess
import json
import os
from datetime import datetime, timedelta
import time

# ==========================
# Lecture des infos du jour
# ==========================
FICHIER_INFO = "quinte_du_jour.json"

if not os.path.exists(FICHIER_INFO):
    raise Exception("Fichier quinte_du_jour.json introuvable. Lance d'abord trouver_quinte.py")

with open(FICHIER_INFO, "r", encoding="utf-8") as f:
    info = json.load(f)

heure_depart_str = info["heure_depart"]  # ex: "20h15"
nom_course = info["nom_course"]

# ==========================
# Calcul des horaires de capture
# ==========================
heure_depart = datetime.strptime(heure_depart_str, "%Hh%M").replace(
    year=datetime.now().year,
    month=datetime.now().month,
    day=datetime.now().day
)

heure_debut   = heure_depart - timedelta(hours=5)      # H-5h
heure_fin     = heure_depart                            # H (départ)
intervalle    = timedelta(minutes=30)

# Construction de la liste des horaires
horaires = []
heure_courante = heure_debut
while heure_courante <= heure_fin:
    horaires.append(heure_courante)
    heure_courante += intervalle

print(f"\n{'='*45}")
print(f"Course : {nom_course}")
print(f"Départ : {heure_depart_str}")
print(f"Première capture : {heure_debut.strftime('%H:%M')}")
print(f"Dernière capture : {heure_fin.strftime('%H:%M')}")
print(f"Nombre de captures prévues : {len(horaires)}")
print(f"{'='*45}\n")

# ==========================
# Boucle de captures
# ==========================
for i, horaire in enumerate(horaires):
    maintenant = datetime.now()

    # Si l'horaire est dans le futur, on attend
    if horaire > maintenant:
        attente = (horaire - maintenant).total_seconds()
        print(f"[{i+1}/{len(horaires)}] Prochaine capture à {horaire.strftime('%H:%M')} "
              f"(dans {int(attente//60)} min {int(attente%60)} sec)...")
        time.sleep(attente)

    # Lancement de la capture
    print(f"\n>>> Capture {i+1}/{len(horaires)} à {datetime.now().strftime('%H:%M')} <<<")
    subprocess.run(["python", "capter_cotes.py"], check=True)

print(f"\n{'='*45}")
print(f"Toutes les captures sont terminées !")
print(f"{'='*45}")