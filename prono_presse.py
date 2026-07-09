import os
import sys
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

soup = BeautifulSoup(response.text, "html.parser")

# Cherche le bon tableau (plus de 5 lignes)
tables = soup.find_all("table")
table = None
for t in tables:
    if len(t.find_all("tr")) > 5:
        table = t
        break

if table is None:
    print("Tableau non disponible pour l'instant.")
    sys.exit(1)  # Code d'erreur 1 = réessayer plus tard

rows = table.find_all("tr")
data = []
for row in rows:
    cols = [cell.get_text(strip=True) for cell in row.find_all(["th", "td"])]
    if cols:
        data.append(cols)

if len(data) < 2:
    print("Tableau vide pour l'instant.")
    sys.exit(1)  # Code d'erreur 1 = réessayer plus tard

header = data[0]
df = pd.DataFrame(data[1:], columns=header)

date_jour = datetime.now().strftime("%Y-%m-%d")
nom_fichier = os.path.join(DOSSIER_SORTIE, f"pronostics_presse_{date_jour}.csv")
df.to_csv(nom_fichier, index=False, encoding="utf-8-sig")

print(f"\n===================================")
print(f"Pronostics récupérés avec succès")
print(f"Date : {date_jour}")
print(f"Nombre de journaux : {len(df)}")
print(f"Fichier : {nom_fichier}")
print(f"===================================\n")
print(df.head())
