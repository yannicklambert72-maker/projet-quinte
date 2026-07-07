import os
from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup

URL = "https://www.boturfers.fr/quinte-du-jour/presse"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0 Safari/537.36"
    )
}
DOSSIER_SORTIE = "historique"
os.makedirs(DOSSIER_SORTIE, exist_ok=True)

print("Connexion au site...")
response = requests.get(URL, headers=HEADERS, timeout=20)
response.raise_for_status()
print("Page téléchargée.")
print("Taille de la page :", len(response.text), "caractères")

soup = BeautifulSoup(response.text, "html.parser")

# Cherche le bon tableau parmi tous
tables = soup.find_all("table")
print("Nombre de tableaux trouvés :", len(tables))

table = None
for i, t in enumerate(tables):
    rows = t.find_all("tr")
    print(f"Tableau {i+1} : {len(rows)} lignes")
    if len(rows) > 5:
        table = t
        print(f"→ Tableau {i+1} sélectionné")
        break

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

date_jour = datetime.now().strftime("%Y-%m-%d")
nom_fichier = os.path.join(DOSSIER_SORTIE, f"pronostics_presse_{date_jour}.csv")
df.to_csv(nom_fichier, index=False, encoding="utf-8-sig")

print("\n===================================")
print("Pronostics récupérés avec succès")
print("Date :", date_jour)
print("Nombre de journaux :", len(df))
print("Fichier :", nom_fichier)
print("===================================\n")
print(df.head())