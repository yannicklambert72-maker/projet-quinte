import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import re
import os
import time
from requests.exceptions import RequestException
import pytz

# ==========================
# Configuration
# ==========================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com/"
}

DOSSIER_SORTIE = "historique_cotes"
URL_GENY = "https://www.geny.com/reunions-courses-pmu"

# ==========================
# Fonction pour faire une requête avec retries exponentiels
# ==========================
def faire_requete(url, max_retries=5, initial_delay=30):
    retry_delay = initial_delay
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=20)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                print(f"[WARNING] 429 reçu pour {url}. Attente {retry_delay}s avant retry...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Délai exponentiel
            else:
                print(f"[ERROR] Code {response.status_code} pour {url}")
                return None
        except RequestException as e:
            print(f"[ERROR] Erreur de requête pour {url} : {e}")
            time.sleep(retry_delay)
            retry_delay *= 2
    print(f"[ERROR] Échec après {max_retries} tentatives pour {url}.")
    return None

# ==========================
# Étape 1 : Trouver le Quinté
# ==========================
print("[INFO] Recherche du Quinté du jour...")
response = faire_requete(URL_GENY)
if response is None:
    print("[ERROR] Impossible de récupérer la page des réunions. Arrêt.")
    exit(1)

soup = BeautifulSoup(response.text, "html.parser")
lien_quinte = soup.find("a", class_="btnQuinte", href=lambda h: h and "partants-pmu" in h)

if lien_quinte is None:
    print("[ERROR] Quinté+ non trouvé. Arrêt.")
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
    print("[ERROR] Heure de départ non trouvée. Arrêt.")
    exit(0)

print(f"[INFO] Quinté trouvé : {nom_course} à {heure_depart_str}")

# ==========================
# Étape 2 : Vérifier la fenêtre H-5h / H
# ==========================
tz_paris = pytz.timezone("Europe/Paris")
maintenant = datetime.now(tz_paris)
heure_depart = datetime.strptime(heure_depart_str, "%Hh%M").replace(
    year=maintenant.year,
    month=maintenant.month,
    day=maintenant.day,
    tzinfo=tz_paris
)

# Vérifie si on est dans la fenêtre H-5h / H
if (maintenant < heure_depart - timedelta(hours=5)) or (maintenant > heure_depart):
    print("[INFO] Hors fenêtre de capture (H-5h / H). Arrêt.")
    exit(0)

print("[INFO] Fenêtre de capture valide → capture en cours...")

# ==========================
# Étape 3 : Capturer les cotes
# ==========================
response2 = faire_requete(url_quinte)
if response2 is None:
    print("[ERROR] Impossible de récupérer la page du Quinté. Arrêt.")
    exit(1)

soup2 = BeautifulSoup(response2.text, "html.parser")
table = soup2.find("table")

if table is None:
    print("[ERROR] Tableau introuvable. Arrêt.")
    exit(0)

rows = table.find_all("tr")
date_jour = maintenant.strftime("%Y-%m-%d")
heure_capture = maintenant.strftime("%H:%M")
data = []

for row in rows[1:]:
    cols = [td.get_text(strip=True) for td in row.find_all("td")]
    if len(cols) == 15:
        data.append({
            "date": date_jour,
            "heure_capture": heure_capture,
            "course": nom_course,
            "depart": heure_depart_str,
            "numero": cols[0],
            "cheval": cols[1].replace('\u200b', '').strip(),
            "jockey": cols[9],
            "entraineur": cols[10],
            "musique": cols[11],
            "valeur": cols[12],
            "cote_pmu": cols[13],
            "cote_geny": cols[14],
        })

if not data:
    print("[ERROR] Aucune donnée extraite.")
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
print(f"[SUCCESS] Cotes capturées à {heure_capture} (Paris)")
print(f"[SUCCESS] Chevaux : {len(data)}")
print(f"[SUCCESS] Fichier : {nom_fichier}")
print(f"===================================")
