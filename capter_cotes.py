import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import json
import os

# ==========================
# Configuration
# ==========================
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0 Safari/537.36"
    )
}
DOSSIER_SORTIE = "historique_cotes"
FICHIER_INFO = "quinte_du_jour.json"

# ==========================
# Lecture des infos du jour
# ==========================
if not os.path.exists(FICHIER_INFO):
    raise Exception("Fichier quinte_du_jour.json introuvable. Lance d'abord trouver_quinte.py")

with open(FICHIER_INFO, "r", encoding="utf-8") as f:
    info = json.load(f)

url = info["url_partants"]
nom_course = info["nom_course"]
heure_depart = info["heure_depart"]
date_jour = info["date"]

print(f"Course : {nom_course} - Départ : {heure_depart}")
print(f"URL    : {url}")

# ==========================
# Téléchargement de la page
# ==========================
print("\nConnexion à Geny.com...")
response = requests.get(url, headers=HEADERS, timeout=20)
response.raise_for_status()
print("Page téléchargée.")

# ==========================
# Extraction du tableau
# ==========================
soup = BeautifulSoup(response.text, "html.parser")
table = soup.find("table")

if table is None:
    raise Exception("Tableau des partants introuvable.")

rows = table.find_all("tr")
heure_capture = datetime.now().strftime("%H:%M")
data = []

for row in rows[1:]:
    cols = [td.get_text(strip=True) for td in row.find_all("td")]
    if len(cols) == 15:  # on ne prend que les vraies lignes de partants
        numero    = cols[0]
        cheval    = cols[1].replace('\ue908', '').strip()  # nettoie les icônes
        jockey    = cols[9]
        entraineur = cols[10]
        musique   = cols[11]
        valeur    = cols[12]
        cote_pmu  = cols[13]
        cote_geny = cols[14]
        data.append({
            "date":          date_jour,
            "heure_capture": heure_capture,
            "course":        nom_course,
            "depart":        heure_depart,
            "numero":        numero,
            "cheval":        cheval,
            "jockey":        jockey,
            "entraineur":    entraineur,
            "musique":       musique,
            "valeur":        valeur,
            "cote_pmu":      cote_pmu,
            "cote_geny":     cote_geny,
        })

if not data:
    raise Exception("Aucune donnée extraite du tableau.")

# ==========================
# Sauvegarde CSV
# ==========================
os.makedirs(DOSSIER_SORTIE, exist_ok=True)
nom_fichier = os.path.join(DOSSIER_SORTIE, f"cotes_{date_jour}.csv")

df_nouveau = pd.DataFrame(data)

if os.path.exists(nom_fichier):
    df_existant = pd.read_csv(nom_fichier, encoding="utf-8-sig")
    df_final = pd.concat([df_existant, df_nouveau], ignore_index=True)
else:
    df_final = df_nouveau

df_final.to_csv(nom_fichier, index=False, encoding="utf-8-sig")

# ==========================
# Résumé
# ==========================
print(f"\n===================================")
print(f"Cotes capturées à {heure_capture}")
print(f"Nombre de chevaux : {len(data)}")
print(f"Fichier : {nom_fichier}")
print(f"===================================\n")
print(df_nouveau[["numero", "cheval", "cote_pmu", "cote_geny"]].to_string(index=False))