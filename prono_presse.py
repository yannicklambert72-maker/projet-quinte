import os
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup

# ==========================
# Configuration
# ==========================

URL = "https://www.boturfers.fr/quinte-du-jour/presse"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0 Safari/537.36"
    )
}

DOSSIER_SORTIE = "historique"

# ==========================
# Création du dossier
# ==========================

os.makedirs(DOSSIER_SORTIE, exist_ok=True)

# ==========================
# Téléchargement
# ==========================

print("Connexion au site...")

response = requests.get(URL, headers=HEADERS, timeout=20)
response.raise_for_status()

print("Page téléchargée.")

# ==========================
# Analyse HTML
# ==========================

soup = BeautifulSoup(response.text, "html.parser")

table = soup.find("table")

if table is None:
    raise Exception("Impossible de trouver le tableau des pronostics.")

rows = table.find_all("tr")

data = []

for row in rows:
    cols = [cell.get_text(strip=True) for cell in row.find_all(["th", "td"])]
    if cols:
        data.append(cols)

if len(data) < 2:
    raise Exception("Le tableau est vide.")

header = data[0]
df = pd.DataFrame(data[1:], columns=header)

# ==========================
# Sauvegarde
# ==========================

date_jour = datetime.now().strftime("%Y-%m-%d")

nom_fichier = os.path.join(
    DOSSIER_SORTIE,
    f"pronostics_presse_{date_jour}.csv"
)

df.to_csv(
    nom_fichier,
    index=False,
    encoding="utf-8-sig"
)

# ==========================
# Résumé
# ==========================

print("\n===================================")
print("Pronostics récupérés avec succès")
print("Date :", date_jour)
print("Nombre de journaux :", len(df))
print("Fichier :", nom_fichier)
print("===================================\n")

print(df.head())