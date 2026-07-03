import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import re
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
URL_GENY = "https://www.geny.com/reunions-courses-pmu"

# ==========================
# Étape 1 : Trouver le Quinté
# ==========================
print("Recherche du Quinté du jour...")
response = requests.get(URL_GENY, headers=HEADERS, timeout=20)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")
lien_quinte = soup.find("a", class_="btnQuinte", href=lambda h: h and "partants-pmu" in h)

if lien_quinte is None:
    print("Quinté+ non trouvé. Arrêt.")
    exit(0)

url_quinte = "https://www.geny.com" + lien_quinte["href"]

# Récupère nom et heure
bloc_course = lien_quinte.find_parent("div", class_="yui-g")
nom_course = ""
heure_depart_str = ""

if bloc_course:
    bloc_nom = bloc_course.find_previous_sibling("div")
    if bloc_nom:
        nom_tag = bloc_nom.find(class_="nomCourse")
        if nom_tag:
            nom_course = nom_tag.get_text(strip=True)
    heure_tag = bloc_course.find("div", class_="btnArrivee")
    if heure_tag:
        match = re.search(r'(\d{2}h\d{2})', heure_tag.get_text())
        if match:
            heure_depart_str = match.group(1)

if not heure_depart_str:
    print("Heure de départ non trouvée. Arrêt.")
    exit(0)

print(f"Quinté trouvé : {nom_course} à {heure_depart_str}")

# ==========================
# Étape 2 : Vérifier la fenêtre H-5h / H
# ==========================
maintenant = datetime.utcnow()  # GitHub tourne en UTC
heure_depart = datetime.strptime(heure_depart_str, "%Hh%M").replace(
    year=maintenant.year,
    month=maintenant.month,
    day=maintenant.day
)

# Conversion heure Paris → UTC (été = UTC+2, hiver = UTC+1)
# On soustrait 2h pour passer de Paris à UTC
heure_depart_utc = heure_depart - timedelta(hours=2)

fenetre_debut = heure_depart_utc - timedelta(hours=5)
fenetre_fin   = heure_depart_utc

print(f"Fenêtre de capture : {fenetre_debut.strftime('%H:%M')} UTC → {fenetre_fin.strftime('%H:%M')} UTC")
print(f"Heure actuelle     : {maintenant.strftime('%H:%M')} UTC")

if not (fenetre_debut <= maintenant <= fenetre_fin):
    print("Hors fenêtre de capture. Rien à faire.")
    exit(0)

print("Dans la fenêtre → capture en cours...")

# ==========================
# Étape 3 : Capturer les cotes
# ==========================
response2 = requests.get(url_quinte, headers=HEADERS, timeout=20)
response2.raise_for_status()

soup2 = BeautifulSoup(response2.text, "html.parser")
table = soup2.find("table")

if table is None:
    print("Tableau introuvable. Arrêt.")
    exit(0)

rows = table.find_all("tr")
date_jour = maintenant.strftime("%Y-%m-%d")
heure_capture = (maintenant + timedelta(hours=2)).strftime("%H:%M")  # on affiche en heure Paris
data = []

for row in rows[1:]:
    cols = [td.get_text(strip=True) for td in row.find_all("td")]
    if len(cols) == 15:
        data.append({
            "date":          date_jour,
            "heure_capture": heure_capture,
            "course":        nom_course,
            "depart":        heure_depart_str,
            "numero":        cols[0],
            "cheval":        cols[1].replace('\ue908', '').strip(),
            "jockey":        cols[9],
            "entraineur":    cols[10],
            "musique":       cols[11],
            "valeur":        cols[12],
            "cote_pmu":      cols[13],
            "cote_geny":     cols[14],
        })

if not data:
    print("Aucune donnée extraite.")
    exit(0)

# ==========================
# Étape 4 : Sauvegarde CSV
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

print(f"\n===================================")
print(f"Cotes capturées à {heure_capture} (Paris)")
print(f"Chevaux : {len(data)}")
print(f"Fichier : {nom_fichier}")
print(f"===================================")